"""Provide an API endpoint for the QuoteMachine."""
# from database import *
# from match_groundtruth import *
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


class Maps(Resource):
    """Return all available site maps."""

    def get(self):
        """Maps list is loaded when server boots up."""
        return maps


api.add_resource(Maps, "/maps", methods=["GET"])

if __name__ == "__main__":
    wsgi.server(eventlet.listen(("localhost", PORT)), app)
