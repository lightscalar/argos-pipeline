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
        "common_name": "water",
        "physiognomy": "N/A",
        "category": "Physical Feature",
        "color_code": "#0e87cc",
    }
    street = {
        "scientific_name": "Roadus Roadius",
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
        "scientific_name": "Rocky Rockinius",
        "codes": ["ROCK"],
        "common_name": "Rock",
        "physiognomy": "N/A",
        "category": "Physical Feature",
        "color_code": "#ada587",
    }

    # Add additional target features.
    targets.append(water)
    targets.append(street)
    targets.append(sand)
    targets.append(rock)

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

    # Now ingest image data. Check to see if we need to.
    maps = map_summaries()

    for cmap in maps:
        print('> Ingesting images for map {cmap["map_id"]}')
        # Get a list of images.
        path_to_images = prepend_argos_root(cmap["path_to_images"])
        images = sorted(glob(f"{path_to_images}/*.JPG"))

        for path_to_image in tqdm(images):
            image_number = extract_image_number(path_to_image)
            image_id = f"{cmap['map_id']}-IMG_{image_number}"
            if get_image(image_id) is None:  # only insert new images.
                info = extract_info(path_to_image)
                image_obj = {
                    "map_id": cmap["map_id"],
                    "image_id": image_id,
                    "lat": info["img_lat"],
                    "lon": info["img_lon"],
                    "height": info["img_height"],
                    "width": info["img_width"],
                }
                imagery_collection.insert_one(image_obj)
