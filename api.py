"""Provide an API endpoint for the QuoteMachine."""
# from database import *
# from match_groundtruth import *
from database import *
from ground_truth_mapping import (
    place_ground_truth_on_map,
    convert_map_coord_to_lat_lon,
    place_ground_truth_on_image,
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
        return global_maps


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


api.add_resource(Maps, "/maps", methods=["GET"])
api.add_resource(Map, "/maps/<map_id>", methods=["GET"])
api.add_resource(Images, "/map-images/<map_id>/", methods=["GET"])
api.add_resource(Image, "/images/<image_id>", methods=["GET"])

if __name__ == "__main__":
    wsgi.server(eventlet.listen(("localhost", PORT)), app)
