"""Utilities for ingesting ground truth and annotation target information."""
from config import *
from database import *
from utils import *

import fiona
import numpy as np
import pandas as pd
import re
import seaborn as sns


# Define regular expression for extracting species code.
REG_EXP = r"(\w+)\s.*"

# Define some nice, random colors.
np.random.seed(0)
colors = list(sns.xkcd_rgb.keys())
np.random.shuffle(colors)


def extract_image_number(path_to_image):
    """Grab the image number from the image name."""
    rgx = r"DJI_(\d+).JPG"
    file_name = path_to_image.split("/")[-1]
    match = re.search(rgx, file_name)
    if match is not None:
        return match[1]


def extract_ground_truth(shape_file="truth/CZM_UAV_WAYPOINTS_2018.shp"):
    """Extract information from the shape files."""
    shapes = fiona.open(shape_file)
    shapes = list(shapes)
    truths = []
    for shape in shapes:
        truth = {}
        truth["geolocation"] = list(shape["geometry"]["coordinates"])
        truth["latlon"] = [
            shape["geometry"]["coordinates"][1],
            shape["geometry"]["coordinates"][0],
        ]
        truth["name"] = shape["properties"]["Name"]
        truth["code"] = re.search(REG_EXP, truth["name"])[1]
        truth["symbol"] = shape["properties"]["Symbol"]
        truth["datetime"] = shape["properties"]["DateTimeS"]
        truth["type"] = "field_collection"
        truths.append(truth)
    return truths


if __name__ == "__main__":

    ingest_ground_truth = False
    ingest_maps = False
    ingest_images = True

    if ingest_ground_truth:
        # Ingest all available annotation targets.
        targets_excel = pd.read_excel(f"{TARGET_FILE}")
        scientific_names = np.unique(list(targets_excel["Scientific Name"]))
        targets = []

        for scientific_name in scientific_names:
            if scientific_name != "nan":
                target = {}
                target["scientific_name"] = scientific_name
                target["codes"] = set([])
                for idx, name in enumerate(targets_excel["Scientific Name"]):
                    if name == scientific_name:
                        target["common_name"] = targets_excel["Common Name"][idx]
                        target["physiognomy"] = targets_excel["PHYSIOGNOMY"][idx]
                        target["category"] = targets_excel["CATEGORY"][idx]
                        target["color_code"] = sns.xkcd_rgb[colors[idx]]
                        codes = targets_excel["Code"][idx].split(" ")
                        for code in codes:
                            target["codes"].add(code)
                targets.append(target)
            else:
                continue

        # Remove sets.
        for target in targets:
            target["codes"] = list(target["codes"])

        water = {
            "scientific_name": "H2O",
            "codes": ["H2O"],
            "common_name": "Water",
            "physiognomy": "N/A",
            "category": "Physical Feature",
            "color_code": "#0e87cc",
        }
        street = {
            "scientific_name": "Roadus roadius",
            "codes": ["ROAD"],
            "common_name": "Road",
            "physiognomy": "N/A",
            "category": "Man-made Feature",
            "color_code": "#070d0d",
        }
        sand = {
            "scientific_name": "Silicon Dioxide",
            "codes": ["DIRT"],
            "common_name": "Sand",
            "physiognomy": "N/A",
            "category": "Physical Feature",
            "color_code": "#8a6e45",
        }
        rock = {
            "scientific_name": "Rocky rockinius",
            "codes": ["ROCK"],
            "common_name": "Rock",
            "physiognomy": "N/A",
            "category": "Physical Feature",
            "color_code": "#ada587",
        }
        florist = {
            "scientific_name": "Joshua floristis",
            "codes": ["JOSH"],
            "common_name": "Josh",
            "physiognomy": "N/A",
            "category": "Animal Wildlife",
            "color_code": "#8e44ad",
        }
        pilot = {
            "scientific_name": "Matthew pilotis",
            "codes": ["MATT"],
            "common_name": "Matt",
            "physiognomy": "N/A",
            "category": "Animal Wildlife",
            "color_code": "#2c3e50",
        }
        animal = {
            "scientific_name": "Animal generalis",
            "codes": ["ANIM"],
            "common_name": "Animal",
            "physiognomy": "N/A",
            "category": "Animal Wildlife",
            "color_code": "#2c3e50",
        }
        leaf_litter = {
            "scientific_name": "Leafy litteris",
            "codes": ["LEAF"],
            "common_name": "Dead Leaf Litter",
            "physiognomy": "N/A",
            "category": "Biological Feature",
            "color_code": "#f39c12",
        }
        automobile = {
            "scientific_name": "Automobilius jeepinius",
            "codes": ["AUTO"],
            "common_name": "Automobile",
            "physiognomy": "N/A",
            "category": "Man-made Feature",
            "color_code": "#2f3640",
        }

        # Add additional target features.
        targets.append(water)
        targets.append(street)
        targets.append(sand)
        targets.append(rock)
        targets.append(florist)
        targets.append(pilot)
        targets.append(animal)
        targets.append(leaf_litter)
        targets.append(automobile)

        # Add the plants to the database.
        target_collection.delete_many({})  # first get rid of all of them.
        target_collection.insert_many(targets)

        # Next we ingest all available ground truth data.
        ground_truths = []
        for shape_file in TRUTH_FILES:
            truths = extract_ground_truth(shape_file)
            ground_truths.extend(truths)

        # Wipe database and insert the ground truth.
        ground_truth_collection.delete_many({})
        ground_truth_collection.insert_many(ground_truths)

    if ingest_maps:
        # Ingest MAPS!
        print("> Finding maps.")
        maps = map_summaries()
        print("> Done.")
        for map_ in maps:
            if get_map(map_["map_id"]) is None:
                map_collection.insert_one(map_)
        # Delete the image collection?
        delete_imagery = False
        if delete_imagery:  # CAUTION! EXPENSIVE TO CREATE
            imagery_collection.delete_many({})

    if ingest_images:
        maps = db.get_maps()
        # For each of the maps available, ingest all available images.
        for itr, cmap in enumerate(maps):
            print(f'> Ingesting images for map {cmap["map_id"]}')
            if itr not in [2, 3]:  # only ingest certain maps... HACK!
                continue
            # Get a list of images.
            path_to_images = prepend_argos_root(cmap["path_to_images"])
            fix_image_filenames(path_to_images)
            images = sorted(glob(f"{path_to_images}/*.JPG"))

            for path_to_image in tqdm(images):
                image_number = extract_image_number(path_to_image)
                image_id = f"{cmap['map_id']}-IMG_{image_number}"
                image_info = parse_image_id(image_id)
                if db.get_image(image_id) is None:  # only insert new images.
                    info = extract_info(path_to_image)
                    image_obj = {
                        "map_id": cmap["map_id"],
                        "image_id": image_id,
                        "lat": info["img_lat"],
                        "lon": info["img_lon"],
                        "height": info["img_height"],
                        "width": info["img_width"],
                        "year": image_info["year"],
                        "month": image_info["month"],
                        "day": image_info["day"],
                        "site": image_info["site"],
                        "path_to_image": image_info["path_to_image"],
                        "path_to_map": image_info["path_to_map"],
                    }
                    # Insert this image object into the database.
                    db.imagery.insert_one(image_obj)
