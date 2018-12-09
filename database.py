"""Utilities for accessing the database, grabbing data, etc."""
from config import *

from bson import ObjectId
from datetime import datetime
from exiftool import ExifTool
from ipdb import set_trace as debug
import numpy as np
import pymongo
from pymongo import MongoClient
import os
import re

# Open up a database instance.
client = MongoClient()

# Connect to the database.
db = client.ARGOS  # database
target_collection = db.targets
ground_truth_collection = db.ground_truth


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
