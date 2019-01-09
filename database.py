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


def extract_tiles_from_annotation(annotation, samples_per_tile):
    """Open up an image and extract tiles."""
    image_dict = parse_image_id(annotation["image_id"])
    try:  # directory may not exist...
        image = plt.imread(prepend_argos_root(image_dict["path_to_image"]))
    except:
        return []
    # Extract tiles.
    rows, cols, chans = image.shape
    row = annotation["alpha"] * rows
    col = annotation["beta"] * cols
    tiles = extract_tiles(image, row, col, num_rotations=samples_per_tile)
    return tiles


def extract_training_tiles(
    scientific_name, tile_size=128, nb_tiles_per_class=1000, samples_per_tile=100
):
    """Extract the tiles to create a training batch."""
    negative_pipeline = [
        {"$sample": {"size": 3 * nb_tiles_per_class}},
        {"$match": {"scientific_name": {"$ne": scientific_name}}},
    ]
    positive_pipeline = [
        {"$sample": {"size": 3 * nb_tiles_per_class}},
        {"$match": {"scientific_name": scientific_name}},
    ]
    negative_samples = list(db.annotations.aggregate(negative_pipeline))
    positive_samples = list(db.annotations.aggregate(positive_pipeline))
    nb_negative = 0
    nb_positive = 0
    X = []
    y = []
    itr = 0
    while nb_positive < nb_tiles_per_class:
        X_ = extract_tiles_from_annotation(positive_samples[itr], samples_per_tile)
        X.extend(X_)
        nb_positive += len(X_)
        y.extend([1] * len(X_))
        itr += 1
        # print(f"{nb_positive/nb_tiles_per_class*100}%")
    itr = 0
    while nb_negative < nb_tiles_per_class:
        X_ = extract_tiles_from_annotation(positive_samples[itr], samples_per_tile)
        X.extend(X_)
        y.extend([0] * len(X_))
        nb_negative += len(X_)
        itr += 1
        # print(f"{nb_negative/nb_tiles_per_class*100}%")
    return np.array(X), np.array(y)


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
        self.annotations.create_index([("scientific_name", pymongo.ASCENDING)])
        if self.imagery.count()>0:
            self.build_image_tree()
        if self.tiles.countr()>0
            self.build_tile_tree()
        if self.ground_truths.count()>0:
            self.build_truth_tree()

    def get_tile(self, tile_id):
        """Retrieve a tile via its tile_id."""
        return self.tiles.find_one({"tile_id": tile_id}, {"_id": 0})

    def get_tiles(self):
        """Return a list of available tiles."""
        tiles = list(self.tiles.find({}, {"_id": 0}))
        return sorted(tiles, key=lambda x: x["tile_id"])

    def insert_tile(self, tile_obj):
        """Add a new tile to the database."""
        self.tiles.insert_one(tile_obj)

    def get_targets(self):
        """Return annotation targets."""
        targets = list(self.targets.find({}, {"_id": 0}))
        return sorted(targets, key=lambda x: x["scientific_name"])

    def get_target(self, target_id):
        """Return specified target (target_id is scientific name)."""
        return self.targets.find_one({"scientific_name": target_id})

    def update_target(self, target):
        """Update the target."""
        target_ = self.targets.find_one({"scientific_name": target["scientific_name"]})
        self.targets.update_one({"_id": target_["_id"]}, {"$set": target}, upsert=False)

    def delete_target(self, target_id):
        """Delete the specified target."""
        self.targets.delete_one({"target_id": target_id})

    def get_maps(self, return_id=False):
        """Return list of maps."""
        if return_id:  # return _id too
            maps = list(self.maps.find({}))
            maps = sorted(maps, key=lambda x: x["start"])
        else:  # skip the _id
            maps = list(self.maps.find({}, {"_id": 0}))
            maps = sorted(maps, key=lambda x: x["start"])
        return maps

    def get_map(self, map_id):
        """Return specified map object."""
        return self.maps.find_one({"map_id": map_id}, {"_id": 0})

    def update_map(self, map_obj):
        """Update the specified map object."""
        self.maps.update_one({"_id": map_obj["_id"]}, {"$set": map_obj}, upsert=False)

    def get_images(self):
        """Return a list of all images."""
        images = list(self.imagery.find({}, {"_id": 0}))
        images = sorted(images, key=lambda x: x["image_id"])
        return images

    def get_image_locations(self):
        """Get image locations from the database."""
        image_locations = list(self.imagery.find({}, {"image_id", "lat", "lon"}))
        image_locations = sorted(image_locations, key=lambda x: x["image_id"])
        return image_locations

    def get_image(self, image_id):
        """Return specified image object."""
        return self.imagery.find_one({"image_id": image_id}, {"_id": 0})

    def get_ground_truths(self):
        """Return all available ground truth."""
        truths = list(self.ground_truths.find({}, {"_id": 0}))
        truths = sorted(truths, key=lambda x: x["datetime"])
        return truths

    def get_ground_truth(self, ground_truth_id):
        """Return all available ground truth."""
        return list(self.ground_truths.find_one({"ground_truth_id": ground_truth_id}))

    def add_ground_truth(self, truth):
        self.ground_truths.insert_one(truth)
        self.build_truth_tree()  # now more truths around, so rebuild

    def delete_ground_truth_for_image(self, image_id):
        """Delete all manual ground truth on specified tile."""
        self.ground_truths.delete_many({"image_id": image_id})
        self.build_truth_tree()  # because there's missing data

    def delete_ground_truth_for_tile(self, tile_id):
        """Delete all manual ground truth on specified tile."""
        self.ground_truths.delete_many({"tile_id": tile_id})
        self.build_truth_tree()  # because there's missing data

    def get_annotation(self, annotation_id):
        """Find specified annotation."""
        return self.annotations.find_one({"annotation_id": annotation_id})

    def get_annotations(self, return_id=False):
        """List all annotations."""
        if return_id:
            annotations = list(self.annotations.find({}))
        else:
            annotations = list(self.annotations.find({}, {"_id": 0}))
        annotations = sorted(annotations, key=lambda x: x["annotation_id"])
        return annotations

    def get_annotations_for_image(self, image_id):
        """List all annotations."""
        return list(self.annotations.find({"image_id": image_id}, {"_id": 0}))

    def delete_annotations_for_image(self, image_id):
        """Delete all annotations for specified tile."""
        self.annotations.delete_many({"image_id": image_id})

    def get_annotations_for_tile(self, tile_id):
        """List all annotations."""
        return list(self.annotations.find({"tile_id": tile_id}, {"_id": 0}))

    def delete_annotations_for_tile(self, tile_id):
        """Delete all annotations for specified tile."""
        self.annotations.delete_many({"tile_id": tile_id})

    def delete_annotation(self, annotation_id):
        """Delete an individual annotation."""
        self.annotations.delete_one({"annotation_id": annotation_id})

    def add_annotation(self, data):
        """Insert an annotation into the database."""
        try:
            self.annotations.insert_one(data)
        except:
            print("> Sorry, that point is already annotated.")

    def update_annotation(self, data):
        """Update an existing annotation."""
        self.annotations.update_one({"_id": data["_id"]}, {"$set": data}, upsert=False)

    def build_image_tree(self):
        """Compute a BallTree object for images in the database."""
        images = self.get_image_locations()
        if len(images) > 0:
            image_locations = np.array([[img["lat"], img["lon"]] for img in images])
            self.image_tree = BallTree(image_locations)
        else:
            self.image_tree = None

    def build_tile_tree(self):
        """Build a BallTree for organizing the tiles in space."""
        tiles = self.get_tiles()
        tile_locations = np.array(
            [
                [(t["north"] + t["south"]) / 2, (t["east"] + t["west"]) / 2]
                for t in tiles
            ]
        )
        if len(tile_locations) > 0:
            self.tile_tree = BallTree(tile_locations)

    def build_truth_tree(self):
        """Compute a BallTree object for all ground truth in the database."""
        truths = self.get_ground_truths()
        truth_locations = np.array([[t["latlon"][0], t["latlon"][1]] for t in truths])
        self.truth_tree = BallTree(truth_locations)


# Create the global database!
db = Database()
