"""Utilities for accessing the database, grabbing data, etc."""
from config import *
from geo_utils import distance_on_earth
from utils import *

from bson import ObjectId
from datetime import datetime
from exiftool import ExifTool
from glob import glob
from ipdb import set_trace as debug
import numpy as np
import pymongo
from pymongo import MongoClient
import os
import re
from sklearn.neighbors import BallTree
from tqdm import tqdm

# Open up a database instance.
client = MongoClient()

# Connect to the database.
db = client.ARGOS  # database
map_collection = db.maps
target_collection = db.targets
ground_truth_collection = db.ground_truth
imagery_collection = db.imagery


def extract_image_number(path_to_image):
    """Grab the image number from the image name."""
    rgx = r"DJI_(\d+).JPG"
    file_name = path_to_image.split("/")[-1]
    match = re.search(rgx, file_name)
    if match is not None:
        return match[1]


def get_image_locations():
    """Get image locations from the database."""
    return list(imagery_collection.find({}, {"image_id", "lat", "lon"}))


def build_truth_tree():
    """Compute a BallTree object for all ground truth in the database."""
    truths = get_ground_truth()
    truth_locations = np.array([[t["latlon"][0], t["latlon"][1]] for t in truths])
    truth_tree = BallTree(truth_locations, metric=distance_on_earth)
    return truth_tree


def build_image_tree():
    """Compute a BallTree object for images in the database."""
    images = get_image_locations()
    image_locations = np.array([[img["lat"], img["lon"]] for img in images])
    image_tree = BallTree(image_locations, metric=distance_on_earth)
    return image_tree


def nearby_images(lat, lon, max_number=10, map_id=None):
    """Find images nearest to specified lat and lon."""
    if map_id is None:
        # If we don't care what map these come from:
        distances, image_list = global_image_tree.query(
            np.array([lat, lon]).reshape(1, -1), k=max_number
        )
        image_list = image_list[0]
        image_ids = [global_image_locations[idx]["image_id"] for idx in image_list]
    else:
        # Ensure we are only grabbing images from specified map.
        distances, image_list = global_image_tree.query(
            np.array([lat, lon]).reshape(1, -1), k=100
        )
        image_list = image_list[0]
        image_ids = []
        for image_idx in image_list:
            image = global_image_locations[image_idx]
            image_info = parse_image_id(image["image_id"])
            if image_info["map_id"] == map_id:
                image_ids.append(image["image_id"])
            else:
                continue
            if len(image_ids) == max_number:
                break
    return image_ids


def get_targets():
    """List all species in the database."""
    target_list = list(target_collection.find({}, {'_id': 0}))
    return target_list


def get_ground_truth():
    """Return all ground truth."""
    return list(ground_truth_collection.find({}, {'_id': 0}))


def get_image(image_id):
    """Find an image based on its unique image_id."""
    image = imagery_collection.find_one({"image_id": image_id}, {'_id': 0})
    return image


def get_map(map_id):
    """Grab a map from the database using its unique ID."""
    map_ = map_collection.find_one({"map_id": map_id}, {'_id': 0})
    return map_


def get_maps():
    """Grab a map from the database using its unique ID."""
    maps = map_collection.find({}, {"_id": 0})
    return list(maps)


"""LOAD SOME THINGS INTO MEMORY THAT ARE USEFUL THROUGHOUT."""
# Load some data that will be used throughout the system.
print("> Building truth/image trees")
# Prepend variables with "global" by convention.
global_ground_truth = get_ground_truth()
if len(global_ground_truth) > 0:
    global_image_locations = get_image_locations()
    global_truth_tree = build_truth_tree()
    global_image_tree = build_image_tree()
    global_maps = get_maps()
print("> Complete")
