"""Utilities for accessing the database, grabbing data, etc."""
from config import *
from geo_utils import distance_on_earth

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


def build_truth_tree():
    """Compute a BallTree object for all ground truth in the database."""
    truths = get_ground_truth()
    truth_locations = np.array([[t["latlon"][0], t["latlon"][1]] for t in truths])
    truth_tree = BallTree(truth_locations, metric=distance_on_earth)
    return truth_tree


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


"""LOAD SOME THINGS INTO MEMORY THAT ARE USEFUL THROUGHOUT."""
# Load some data that will be used throughout the system.
print("Building truth tree")
ground_truth = get_ground_truth()
truth_tree = build_truth_tree()
