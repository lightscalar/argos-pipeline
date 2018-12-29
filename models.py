"""Implements classes for import models: tiles, maps, etc."""
from database import *

import numpy as np


class Map:
    """Handles maps, including all necessary georeferencing, ground truth discovery, etc."""

    def __init__(self, map_obj):
        """Ingest all the map stuff."""
        for key, val in map_obj.items():
            self.__dict__[key] = val

    def get_latitude_boundaries(self, boundaries_to_use="small_map_boundaries"):
        """Returns north/south boundaries of specified map."""
        try:
            bnd = self.__dict__[boundaries_to_use]
        except:
            raise ValueError("No boundary information is available for this map.")
        return bnd["north"], bnd["south"]

    def get_longitude_boundaries(self, boundaries_to_use="small_map_boundaries"):
        """Returns north/south boundaries of specified map."""
        try:
            bnd = self.__dict__[boundaries_to_use]
        except:
            raise ValueError("No boundary information is available for this map.")
        return bnd["east"], bnd["west"]

    def alpha_to_latitude(self, alpha, boundaries_to_use="small_map_boundaries"):
        """Convert alpha (fraction of image height) to latitude."""
        north, south = self.get_latitude_boundaries(boundaries_to_use)
        return north * (1 - alpha) + south * alpha

    def latitude_to_alpha(self, lat, boundaries_to_use="small_map_boundaries"):
        """Convert latitude to image alpha."""
        north, south = self.get_latitude_boundaries(boundaries_to_use)
        return (lat - north) / (south - north)

    def beta_to_longitude(self, beta, boundaries_to_use="small_map_boundaries"):
        """Convert beta (fraction of image width) to longitude."""
        east, west = self.get_longitude_boundaries(boundaries_to_use)
        return west * (1 - beta) + east * beta

    def longitude_to_beta(self, lon, boundaries_to_use="small_map_boundaries"):
        """Convert longitude to beta."""
        east, west = self.get_longitude_boundaries(boundaries_to_use)
        return (lon - west) / (east - west)

    def to_lat_lon(self, alpha, beta, boundaries_to_use="small_map_boundaries"):
        """Convert (alpha, beta) in image to latitude/longitude."""
        lat = self.alpha_to_latitude(alpha, boundaries_to_use="small_map_boundaries")
        lon = self.beta_to_longitude(beta, boundaries_to_use="small_map_boundaries")
        return lat, lon

    def to_alpha_beta(self, lat, lon):
        """Convert latitude/longitude to alpha/beta."""
        alpha = self.latitude_to_alpha(lat, boundaries_to_use="small_map_boundaries")
        beta = self.longitude_to_beta(lon, boundaries_to_use="small_map_boundaries")
        return alpha, beta

    def find_ground_truth(self):



class Tile:
    """Handles georeferencing of tile objects."""

    def __init__(self, tile_dict):
        """Build a tile object."""
        for key, val in tile_dict.items():
            self.__dict__[key] = val

    def alpha_to_latitude(self, alpha):
        """Convert alpha (fraction of image height) to latitude."""
        return self.north * (1 - alpha) + self.south * alpha

    def latitude_to_alpha(self, lat):
        """Convert latitude to image alpha."""
        return (lat - self.north) / (self.south - self.north)

    def beta_to_longitude(self, beta):
        """Convert beta (fraction of image width) to longitude."""
        return self.west * (1 - beta) + self.east * beta

    def longitude_to_beta(self, lon):
        """Convert longitude to beta."""
        return (lon - self.west) / (self.east - self.west)

    def to_lat_lon(self, alpha, beta):
        """Convert (alpha, beta) in image to latitude/longitude."""
        lat = self.alpha_to_latitude(alpha)
        lon = self.beta_to_longitude(beta)
        return lat, lon

    def to_alpha_beta(self, lat, lon):
        """Convert latitude/longitude to alpha/beta."""
        alpha = self.latitude_to_alpha(lat)
        beta = self.longitude_to_beta(lon)
        return alpha, beta
