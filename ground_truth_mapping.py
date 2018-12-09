"""Utilities for mapping ground truth to maps and high-resolution imagery."""
from database import *
from geo_utils import *
from sklearn.neighbors import BallTree


def truth_tree():
    """Compute a BallTree object for all ground truth in the database."""
    truths = get_ground_truth()
    truth_locations = np.array([[t["latlon"][0], t["latlon"][1]] for t in truths])
    truth_tree = BallTree(truth_locations, metric=distance_on_earth)
    return truth_tree


def place_ground_truth_on_map(map_obj):
    """Returns list of (row,col) coordinates for placement on small map."""
    path_to_geomap = map_obj["path_to_geomap"]
    path_to_geomap = f"{ARGOS_ROOT}/path_to_geomap"
    ds = gdal.Open(path_to_geomap)
    lon, lat = pixel_to_coord(ds, ds.RasterXSize / 2, ds.RasterYSize / 2)
    return lat, lon


if __name__ == "__main__":
    from utils import map_summaries

    # Place ground truth on a map.
    maps = map_summaries()
    lat, lon = place_ground_truth_on_map(maps[0])
