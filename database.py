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


class Database:
    """Handle resource CRUD."""

    def __init__(self):
        """Define collections."""
        client = MongoClient()
        db = client.ARGOS

        # Create maps collection.
        self.maps = db.maps
        self.maps.create_index([("map_id", pymongo.ASCENDING)], unique=True)

        # Create target collection.
        self.targets = db.targets
        self.targets.create_index([("scientific_name", pymongo.ASCENDING)], unique=True)

        # Create ground truth collection.
        self.ground_truths = db.ground_truth
        # self.ground_truths.create_index([("datetime", pymongo.ASCENDING)], unique=True)

        # Create the imagery collection.
        self.imagery = db.imagery
        self.imagery.create_index([("image_id", pymongo.ASCENDING)], unique=True)

        # Create the imagery collection.
        self.tiles = db.tiles
        self.tiles.create_index([("tile_id", pymongo.ASCENDING)], unique=True)

        # Annotations collection.
        self.annotations = db.annotations
        self.annotations.create_index(
            [("annotation_id", pymongo.ASCENDING)], unique=True
        )
        self.build_image_tree()
        self.build_truth_tree()

    def get_tiles(self):
        """Return a list of available tiles."""
        return list(self.tiles.find({}, {"_id": 0}))

    def insert_tile(self, tile_obj):
        """Add a new tile to the database."""
        self.tiles.insert_one(tile_obj)

    def get_targets(self):
        """Return annotation targets."""
        return list(self.targets.find({}))

    def get_target(self, target_id):
        """Return specified target (target_id is scientific name)."""
        return self.targets.find_one({"scientific_name": target_id})

    def get_maps(self, return_id=False):
        """Return list of maps."""
        if return_id:  # return _id too
            return list(self.maps.find({}))
        else:  # skip the _id
            return list(self.maps.find({}, {"_id": 0}))

    def get_map(self, map_id):
        """Return specified map object."""
        return self.maps.find_one({"map_id": map_id})

    def update_map(self, map_obj):
        """Update the specified map object."""
        self.maps.update_one({"_id": map_obj["_id"]}, {"$set": map_obj}, upsert=False)

    def get_images(self):
        """Return a list of all images."""
        return list(self.imagery.find({}))

    def get_image_locations(self):
        """Get image locations from the database."""
        image_locations = list(self.imagery.find({}, {"image_id", "lat", "lon"}))
        image_locations = sorted(image_locations, key=lambda x: x["image_id"])
        return image_locations

    def get_image(self, image_id):
        """Return specified image object."""
        return self.imagery.find_one({"image_id": image_id})

    def get_ground_truths(self):
        """Return all available ground truth."""
        truths = list(self.ground_truths.find({}))
        truths = sorted(truths, key=lambda x: x["datetime"])
        return truths

    def get_ground_truth(self, ground_truth_id):
        """Return all available ground truth."""
        return list(self.ground_truths.find_one({"ground_truth_id": ground_truth_id}))

    def get_annotations(self):
        """List all annotations."""
        return list(self.annotations.find({}))

    def get_annotations_by_image_id(self, image_id):
        """Return all annotations associated with specific image."""
        return list(self.annotations.find({"image_id": image_id}))

    def build_image_tree(self):
        """Compute a BallTree object for images in the database."""
        images = self.get_image_locations()
        if len(images) > 0:
            image_locations = np.array([[img["lat"], img["lon"]] for img in images])
            self.image_tree = BallTree(image_locations)
        else:
            self.image_tree = None

    def build_truth_tree(self):
        """Compute a BallTree object for all ground truth in the database."""
        truths = self.get_ground_truths()
        truth_locations = np.array([[t["latlon"][0], t["latlon"][1]] for t in truths])
        self.truth_tree = BallTree(truth_locations)


# Create the global database!
db = Database()

# # Open up a database instance.
# client = MongoClient()

# # Connect to the database.
# db = client.ARGOS  # database

# # Maps collection.
# map_collection = db.maps

# # Target collection.
# target_collection = db.targets

# # Ground truth collection.
# ground_truth_collection = db.ground_truth
# # ground_truth_collection.create_index([("datetime", pymongo.ASCENDING)], unique=True)

# # Imagery collection.
# imagery_collection = db.imagery
# imagery_collection.create_index([("image_id", pymongo.ASCENDING)], unique=True)

# # Annotations collection.
# annotations_collection = db.annotations
# annotations_collection.create_index([("annotation_id", pymongo.ASCENDING)], unique=True)


# def extract_image_number(path_to_image):
#     """Grab the image number from the image name."""
#     rgx = r"DJI_(\d+).JPG"
#     file_name = path_to_image.split("/")[-1]
#     match = re.search(rgx, file_name)
#     if match is not None:
#         return match[1]


# def get_image_locations():
#     """Get image locations from the database."""
#     image_locations = list(imagery_collection.find({}, {"image_id", "lat", "lon"}))
#     image_locations = sorted(image_locations, key=lambda x: x["image_id"])
#     return image_locations


# def build_truth_tree():
#     """Compute a BallTree object for all ground truth in the database."""
#     truths = get_ground_truth()
#     truth_locations = np.array([[t["latlon"][0], t["latlon"][1]] for t in truths])
#     truth_tree = BallTree(truth_locations)
#     return truth_tree


# def build_image_tree():
#     """Compute a BallTree object for images in the database."""
#     images = get_image_locations()
#     if len(images) > 0:
#         image_locations = np.array([[img["lat"], img["lon"]] for img in images])
#         image_tree = BallTree(image_locations)
#         return image_tree
#     else:
#         return None


# def nearby_images(lat, lon, max_number=10, map_id=None):
#     """Find images nearest to specified lat and lon."""
#     image_locations = get_image_locations()
#     if map_id is None:
#         # If we don't care what map these come from:
#         distances, image_list = ball_trees["image"].query(
#             np.array([lat, lon]).reshape(1, -1), k=max_number
#         )
#         image_list = image_list[0]
#         image_ids = [image_locations[idx]["image_id"] for idx in image_list]
#     else:
#         # Ensure we are only grabbing images from specified map.
#         distances, image_list = ball_trees["image"].query(
#             np.array([lat, lon]).reshape(1, -1), k=100
#         )
#         image_list = image_list[0]
#         image_ids = []
#         for image_idx in image_list:
#             image = image_locations[image_idx]
#             image_info = parse_image_id(image["image_id"])
#             if image_info["map_id"] == map_id:
#                 image_ids.append(image["image_id"])
#             else:
#                 continue
#             if len(image_ids) == max_number:
#                 break
#     return image_ids


# def get_targets():
#     """List all species in the database."""
#     target_list = list(target_collection.find({}, {"_id": 0}))
#     return target_list


# def get_ground_truth():
#     """Return all ground truth."""
#     gtr = list(ground_truth_collection.find({}, {"_id": 0}))
#     gtr = sorted(gtr, key=lambda x: x["datetime"])
#     return gtr


# def get_image(image_id):
#     """Find an image based on its unique image_id."""
#     image = imagery_collection.find_one({"image_id": image_id}, {"_id": 0})
#     return image


# def get_map(map_id):
#     """Grab a map from the database using its unique ID."""
#     map_ = map_collection.find_one({"map_id": map_id}, {"_id": 0})
#     return map_


# def get_maps():
#     """Grab a map from the database using its unique ID."""
#     maps = map_collection.find({}, {"_id": 0})
#     return list(maps)


# """LOAD SOME THINGS INTO MEMORY THAT ARE USEFUL THROUGHOUT."""
# # Load some data that will be used throughout the system.
# print("> Building truth/image trees")
# ground_truth = get_ground_truth()
# ball_trees = {}
# if len(ground_truth) > 0:
#     ball_trees["truth"] = build_truth_tree()
#     ball_trees["image"] = build_image_tree()
# print("> Complete")
