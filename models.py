"""Implements classes for import models: tiles, maps, etc."""
from database import *

import numpy as np


def create_machine_truth(truth):
    """Create a new ground truth annotation."""
    alpha = truth["alpha"]
    beta = truth["beta"]
    tile_id = truth["image_id"]
    tile_dict = db.get_tile(tile_id)
    tile_model = TileModel(tile_dict)

    # Extract geomapping information.
    lat, lon = tile_model.to_lat_lon(alpha, beta)
    truth_obj = {
        "latlon": [lat, lon],
        "code": truth["code"],
        "symbol": "",
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "type": "computer_annotated",
        "tile_id": tile_id,
    }
    return truth_obj


def match_truth_to_target(truth, targets):
    """Augment the truth with scientific name, color code, etc."""
    target_found = False
    for target in targets:
        if truth["code"] in target["codes"]:
            truth["scientific_name"] = target["scientific_name"]
            truth["common_name"] = target["common_name"]
            truth["color_code"] = target["color_code"]
            target_found = True
    if target_found:
        return truth
    else:
        return None


def find_unique_truth(nearby_truth_list):
    """Make a list of all unique ground truth targets present."""
    targets_ = []
    unique_targets = []
    for t in nearby_truth_list:
        if t["scientific_name"] not in targets_:
            targets_.append(t["scientific_name"])
            unique_targets.append(t)
    return unique_targets


class MapModel:
    """Handles maps, including all necessary georeferencing, ground truth discovery, etc."""

    def __init__(self, map_obj):
        """Ingest all the map stuff."""
        self.map_obj = map_obj
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

    def in_map(self, alpha, beta):
        """Determine whether specified point is in the map, or not."""
        return (alpha >= 0) * (alpha <= 1) * (beta >= 0) * (beta <= 1)

    def find_ground_truth(self):
        """Find ground truth present on the map and map it to alpha/beta values."""
        lat, lon = self.to_lat_lon(0.5, 0.5)  # lat/lon of map center
        _, ordered_truth = db.truth_tree.query([[lat, lon]], k=300)
        ordered_truth = ordered_truth[0]
        truths = db.get_ground_truths()
        targets = db.get_targets()
        nearby_truths = []
        for truth_idx in ordered_truth:
            truth = truths[truth_idx]
            lat, lon = truth["latlon"]
            alpha, beta = self.to_alpha_beta(lat, lon)
            if not self.in_map(alpha, beta):
                break
            truth = match_truth_to_target(truth, targets)
            if truth is not None:
                truth["alpha"] = alpha  # fraction of image height (rows)
                truth["beta"] = beta  # fraction of image width (cols)
                nearby_truths.append(truth)
        unique_truths = find_unique_truth(nearby_truths)
        return nearby_truths, unique_truths

    def package(self):
        """Return a JSON package for transport to the client."""
        nearby_truth, unique_truth = self.find_ground_truth()
        package = {}
        package["map"] = self.map_obj
        package["truth"] = {"nearby": nearby_truth, "unique": unique_truth}
        return package

    def find_nearest_tile(self, alpha, beta, nb_tiles=100):
        """Return ID of tile nearest given alpha/beta coordinates."""
        lat, lon = self.to_lat_lon(alpha, beta)
        all_tiles = db.get_tiles()
        _, nearest_tiles = db.tile_tree.query([[lat, lon]], k=nb_tiles)
        nearest_tiles = nearest_tiles[0]
        for tile_idx in nearest_tiles:
            tile = all_tiles[tile_idx]
            t = TileModel(tile)
            if t.map_id == self.map_id:  # ensure that tile is from current map
                return t


class TileModel:
    """Handles georeferencing, etc., of tile objects."""

    def __init__(self, tile_dict):
        """Build a tile object."""
        self.tile_obj = tile_dict
        for key, val in tile_dict.items():
            self.__dict__[key] = val

    @property
    def map_id(self):
        """Generate map_id from the tile_id."""
        tile_id_list = self.tile_id.split("-")
        map_id = "-".join(tile_id_list[:-1])
        return map_id

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

    def in_tile(self, alpha, beta):
        """Determine whether specified point is in the map, or not."""
        return (alpha >= 0) * (alpha <= 1) * (beta >= 0) * (beta <= 1)

    def find_ground_truth(self):
        """Find ground truth present on the map and map it to alpha/beta values."""
        lat, lon = self.to_lat_lon(0.5, 0.5)  # lat/lon of map center
        _, ordered_truth = db.truth_tree.query([[lat, lon]], k=300)
        ordered_truth = ordered_truth[0]
        truths = db.get_ground_truths()
        targets = db.get_targets()
        nearby_truths = []
        for truth_idx in ordered_truth:
            truth = truths[truth_idx]
            lat, lon = truth["latlon"]
            alpha, beta = self.to_alpha_beta(lat, lon)
            if not self.in_tile(alpha, beta):
                break
            truth = match_truth_to_target(truth, targets)
            if truth is not None:
                truth["alpha"] = alpha  # fraction of image height (rows)
                truth["beta"] = beta  # fraction of image width (cols)
                nearby_truths.append(truth)
        unique_truths = find_unique_truth(nearby_truths)
        return nearby_truths, unique_truths

    def package(self):
        """Return JSON-serialiable package for client consumption."""
        nearby_truth, unique_truth = self.find_ground_truth()
        package = {}
        package["tile"] = self.tile_obj
        package["tile"]["map_id"] = self.map_id
        package["truth"] = {"nearby": nearby_truth, "unique": unique_truth}
        return package

    def get_neighbor(self, direction):
        """Get the neighboring tile in the specified direction."""
        map_id = self.map_id
        tiles = db.get_tiles()
        if direction == "north":
            alpha = -0.5
            beta = 0.5
        elif direction == "south":
            alpha = 1.5
            beta = 0.5
        elif direction == "west":
            alpha = 0.5
            beta = -0.5
        elif direction == "east":
            alpha = 0.5
            beta = 1.5
        lat, lon = self.to_lat_lon(alpha, beta)
        _, ordered_truth = db.tile_tree.query([[lat, lon]], k=100)
        ordered_truth = ordered_truth[0]
        for idx in ordered_truth:
            tile = TileModel(tiles[idx])
            if tile.map_id == map_id:
                return tile


if __name__ == "__main__":

    maps = db.get_maps()
    mp = maps[4]
    mp = MapModel(mp)
