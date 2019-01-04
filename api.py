"""Provide an API endpoint for the QuoteMachine."""
from database import *
from models import *
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
        return db.get_maps()


class Map(Resource):
    """Return all available site maps."""

    def get(self, map_id):
        """Maps list is loaded when server boots up."""
        tgt_map = db.get_map(map_id)
        map_obj = MapModel(tgt_map)
        return map_obj.package()


class GroundTruths(Resource):
    """Handle creation of ground truth, etc."""

    def post(self):
        """Create a new post-field ground truth point."""
        data = request.json
        new_truth = create_machine_truth(data)
        db.add_ground_truth(new_truth)
        return 200


class GroundTruth(Resource):
    """Handle ground truth deletion."""

    def delete(self, image_id):
        """Delete all post-field ground truth from given image."""
        db.delete_ground_truth_for_image(image_id)
        return 200


class Targets(Resource):
    """Return a list of annotation targets."""

    def get(self):
        """Grab existing global targets."""
        return db.get_targets()

    def post(self):
        """Add a new target."""
        target = request.json
        try:
            db.targets.insert_one(target)
        except:
            print("Sorry. Target already exists.")
        targets = db.get_targets()
        return targets, 200


class Target(Resource):
    """Handle editing of targets."""

    def put(self, target_id):
        """Update a target."""
        target = request.json
        db.update_target(target)
        targets = db.get_targets()
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
        alpha = float(request.args.get("alpha"))  # height
        beta = float(request.args.get("beta"))  # width
        cmap = db.get_map(map_id)
        map_model = MapModel(cmap)
        nearest_image = map_model.find_nearest_image(alpha, beta)
        return [nearest_image.image_id]


class Image(Resource):
    """Return info and ground truth associated with a single image."""

    def get(self, image_id):
        """Load the image and map associated ground truth."""
        image_dict = db.get_image(image_id)
        image_model = ImageModel(image_dict)
        return image_model.package()


class Navigate(Resource):
    """Navigate to a neighboring image."""

    def get(self, image_id):
        """Return the neighboring image in the specified direction."""
        direction = request.args.get("direction")  # height
        image_dict = db.get_image(image_id)
        image_model = ImageModel(image_dict)
        neighbor_image = image_model.get_neighbor(direction)
        return neighbor_image.package()


class ImageAnnotations(Resource):
    """Handle annotation saving, etc."""

    def get(self, image_id):
        annotations = db.annotations.find({"image_id": image_id})
        return annotations

    def post(self):
        """Add the provided annotation to the database."""
        data = request.json
        db.add_annotation(data)
        return db.get_annotations_for_image(data["image_id"])


class ImageAnnotation(Resource):
    """Returns annotations for a specific image."""

    def get(self, image_id):
        """Return all available annotations for a specfic image."""
        return db.get_annotations_for_image(image_id)

    def delete(self, image_id):
        """Delete specified annotation from database."""
        db.delete_annotations_for_image(image_id)
        return db.get_annotations_for_image(image_id), 200


class Annotation(Resource):
    """Handle an individual annotation"""

    def delete(self, annotation_id):
        """Delete an individual annotation."""
        annotation = db.get_annotation(annotation_id)
        db.delete_annotation(annotation_id)
        image_id = annotation["image_id"]
        return db.get_annotations_for_image(image_id)


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
api.add_resource(Navigate, "/images/navigate/<image_id>", methods=["GET"])


if __name__ == "__main__":
    from getpass import getuser

    if getuser() == "mjl":
        wsgi.server(eventlet.listen(("localhost", PORT)), app)
    elif getuser() == "mlewis":  # we're on Zee
        wsgi.server(eventlet.listen(("192.168.40.5", PORT)), app)
