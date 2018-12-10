"""Provide an API endpoint for the QuoteMachine."""
# from database import *
# from match_groundtruth import *
from ground_truth_mapping import place_ground_truth_on_map
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


maps = map_summaries()


def find_map(map_id):
    """Cycle through available maps to find a match."""
    for cmap in maps:
        if cmap["map_id"] == map_id:
            return cmap


class Maps(Resource):
    """Return all available site maps."""

    def get(self):
        """Maps list is loaded when server boots up."""
        return maps


class Map(Resource):
    """Return all available site maps."""

    def get(self, map_id):
        """Maps list is loaded when server boots up."""
        tgt_map = find_map(map_id)
        truth = place_ground_truth_on_map(tgt_map)
        return {
            "map": tgt_map,
            "nearby_truth": truth["nearby_truth"],
            "unique_truth": truth["unique_truth"],
            "image_rows": truth["image_rows"],
            "image_cols": truth["image_cols"],
        }


api.add_resource(Maps, "/maps", methods=["GET"])
api.add_resource(Map, "/maps/<map_id>", methods=["GET"])

if __name__ == "__main__":
    wsgi.server(eventlet.listen(("localhost", PORT)), app)
