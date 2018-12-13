"""Utilities for accessing the database, grabbing data, etc."""
from config import *
from database import *
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


def nearby_images(lat, lon, max_number=10):
    """Find images nearest to specified lat and lon."""
    distances, image_list = global_image_tree.query(
        np.array([lat, lon]).reshape(1, -1), k=max_number
    )
    image_list = image_list[0]
    image_ids = [global_image_locations[idx]["image_id"] for idx in image_list]
    return image_ids


def get_targets():
    """List all species in the database."""
    target_list = list(target_collection.find({}))
    # ObjectId is not serializable, so...
    for target in target_list:
        target["_id"] = str(target["_id"])
    return target_list


def get_ground_truth():
    """Return all ground truth."""
    return list(ground_truth_collection.find({}))


def get_image(image_id):
    """Find an image based on its unique image_id."""
    image = imagery_collection.find_one({"image_id": image_id})
    return image


def get_map(map_id):
    """Return the map object associated with specified map_id."""
    for map_ in global_maps:
        if map_["map_id"] == map_id:
            return map_


"""LOAD SOME THINGS INTO MEMORY THAT ARE USEFUL THROUGHOUT."""
# Load some data that will be used throughout the system.
print("> Building truth/image trees")
# Prepend variables with "global" by convention.
global_ground_truth = get_ground_truth()
global_image_locations = get_image_locations()
global_truth_tree = build_truth_tree()
global_image_tree = build_image_tree()
global_maps = map_summaries()
print("> Complete")
