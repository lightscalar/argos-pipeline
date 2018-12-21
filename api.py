"""Provide an API endpoint for the QuoteMachine."""
# from match_groundtruth import *
from database import *
from ground_truth_mapping import (
    place_ground_truth_on_map,
    convert_map_coord_to_lat_lon,
    place_ground_truth_on_image,
    create_machine_truth,
)
from utils import *

from bson import ObjectId
from glob import glob
import eventlet
from eventlet import wsgi
from flask import Flask, request, jsonify, Response, make_response, send_file
from flask_restful import Resource, Api
from flask_cors import CORS
from ipdb import set_trace as debug
import json
import os
from tqdm import tqdm
from skimage.io import imread, imsave
import io


PORT = 2005
app = Flask(__name__)
CORS(app)
api = Api(app)


class Maps(Resource):
    """Return all available site maps."""

    def get(self):
        """Maps list is loaded when server boots up."""
        maps = list(map_collection.find({}, {"_id": 0}))
        return sorted(maps, key=lambda x: x["start"])


class Map(Resource):
    """Return all available site maps."""

    def get(self, map_id):
        """Maps list is loaded when server boots up."""
        tgt_map = get_map(map_id)
        truth = place_ground_truth_on_map(tgt_map)
        return {
            "map": tgt_map,
            "nearby_truth": truth["nearby_truth"],
            "unique_truth": truth["unique_truth"],
            "image_rows": truth["image_rows"],
            "image_cols": truth["image_cols"],
        }


class GroundTruths(Resource):
    """Handle creation of ground truth, etc."""

    def post(self):
        """Create a new post-field ground truth point."""
        data = request.json
        new_truth = create_machine_truth(data)
        ground_truth_collection.insert_one(new_truth)
        ball_trees["truth"] = build_truth_tree()  # rebuild truth ball tree
        return 200


class GroundTruth(Resource):
    """Handle ground truth deletion."""

    def delete(self, image_id):
        """Delete all post-field ground truth from given image."""
        ground_truth_collection.delete_many({"image_id": image_id})
        return 200


class Targets(Resource):
    """Return a list of annotation targets."""

    def get(self):
        """Grab existing global targets."""
        return sorted(
            target_collection.find({}, {"_id": 0}), key=lambda x: x["scientific_name"]
        )

    def post(self):
        """Add a new target."""
        target = request.json
        try:
            target_collection.insert_one(target)
        except:
            print("Sorry. Target already exists.")
        targets = list(target_collection.find({}, {"_id": 0}))
        return targets, 200


class Target(Resource):
    """Handle editing of targets."""

    def put(self, target_id):
        """Update a target."""
        target = request.json
        out = target_collection.update_one(
            {"scientific_name": target["scientific_name"]},
            {"$set": target},
            upsert=False,
        )
        targets = list(target_collection.find({}, {"_id": 0}))
        return targets, 200

    def delete(self, target_id):
        """Delete the specified target."""
        target_collection.delete_one({"scientific_name": target_id})
        targets = list(target_collection.find({}, {"_id": 0}))
        return targets, 200


class Images(Resource):
    """Returns a list of nearby images"""

    def get(self, map_id):
        """Return a list of all images near given lat/lon on given map."""
        col = float(request.args.get("col"))
        row = float(request.args.get("row"))
        map_lat, map_lon = convert_map_coord_to_lat_lon(col, row, map_id)
        return nearby_images(map_lat, map_lon, map_id=map_id)


class Image(Resource):
    """Return info and ground truth associated with a single image."""

    def get(self, image_id):
        """Load the image and map associated ground truth."""
        image_obj = get_image(image_id)
        image_obj["truth"] = place_ground_truth_on_image(image_obj)
        return image_obj


class ImageAnnotations(Resource):
    """Handle annotation saving, etc."""

    def get(self, image_id):
        annotations = annotation_collection.find({"image_id": image_id})
        return annotations

    def post(self):
        """Add the provided annotation to the database."""
        data = request.json
        try:
            annotations_collection.insert_one(data)
        except:
            print("Sorry, that point is already annotated.")
        annotations = list(
            annotations_collection.find({"image_id": data["image_id"]}, {"_id": 0})
        )
        return annotations


class ImageAnnotation(Resource):
    """Returns annotations for a specific image."""

    def get(self, image_id):
        annotations = list(
            annotations_collection.find({"image_id": image_id}, {"_id": 0})
        )
        return annotations

    def delete(self, image_id):
        """Delete specified annotation from database."""
        annotations_collection.delete_many({"image_id": image_id})
        return list(annotations_collection.find({"image_id": image_id})), 200


class Annotation(Resource):
    """Handle an individual annotation"""

    def delete(self, annotation_id):
        """Delete an individual annotation."""
        annotation = annotations_collection.find_one({"annotation_id": annotation_id})
        image_id = annotation["image_id"]
        annotations_collection.delete_one({"annotation_id": annotation_id})
        return list(annotations_collection.find({"image_id": image_id}, {"_id": 0}))


# Define endpoints.
api.add_resource(Maps, "/maps", methods=["GET"], strict_slashes=False)
api.add_resource(Map, "/maps/<map_id>", methods=["GET"])
api.add_resource(Images, "/map-images/<map_id>/", methods=["GET"])
api.add_resource(Image, "/images/<image_id>", methods=["GET"])
api.add_resource(Targets, "/targets", methods=["GET", "POST"])
api.add_resource(Target, "/targets/<target_id>", methods=["GET", "PUT", "DELETE"])
api.add_resource(ImageAnnotations, "/annotations", methods=["GET", "POST"])
api.add_resource(ImageAnnotation, "/annotations/<image_id>", methods=["GET", "DELETE"])
api.add_resource(Annotation, "/annotation/<annotation_id>", methods=["DELETE"])
api.add_resource(GroundTruths, "/truths", methods=["POST"])
api.add_resource(GroundTruth, "/truths/<image_id>", methods=["DELETE"])


if __name__ == "__main__":
    from getpass import getuser

    if getuser() == 'mjl':
        wsgi.server(eventlet.listen(("localhost", PORT)), app)
    elif getuser() == 'mlewis': # we're on Zee
        wsgi.server(eventlet.listen(("http://argos.michaero.com", PORT)), app)

