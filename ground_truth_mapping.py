"""Utilities for mapping ground truth to maps and high-resolution imagery."""
from database import *
from geo_utils import *
from georeferencer import *
from utils import prepend_argos_root, map_summaries

from ipdb import set_trace as debug
from PIL import Image


def match_truth_to_target(truth, targets):
    """Augment the truth with scientific name, color code, etc."""
    for target in targets:
        if truth["code"] in target["codes"]:
            truth["scientific_name"] = target["scientific_name"]
            truth["common_name"] = target["common_name"]
    return truth


def place_ground_truth_on_map(map_obj):
    """Returns list of (row,col) coordinates for placement on small map."""
    # Note this assumes we've imported truth_tree and ground_truth from database.
    path_to_geomap = prepend_argos_root(map_obj["path_to_geomap"])
    path_to_map = prepend_argos_root(map_obj["path_to_map"])

    # Open small map to get size.
    small_map = Image.open(path_to_map)
    small_rows, small_cols = small_map.size

    # Open georeference information on the map.
    ds = gdal.Open(path_to_geomap)
    large_rows, large_cols = ds.RasterYSize, ds.RasterXSize

    # Compute large/small conversion factors.
    row_convert = small_rows / large_rows
    col_convert = small_cols / large_cols

    # Find center of the map in lat/lon
    map_lon, map_lat = pixel_to_coord(ds, ds.RasterXSize / 2, ds.RasterYSize / 2)

    # Find all ground truth nearby (nearest k).
    _, nearby_truth = truth_tree.query([[map_lat, map_lon]], k=100)

    # Compile a list of ground truth attached to this map.
    targets = get_targets()
    nearby_truth_list = []
    for truth_idx in nearby_truth[0]:
        tru = ground_truth[truth_idx]
        lat, lon = tru["latlon"]
        col, row = coord_to_pixel(ds, lon, lat)
        gt = {"col": col * col_convert, "row": row * row_convert, "code": tru["code"]}
        gt = match_truth_to_target(gt, targets)
        nearby_truth_list.append(gt)

    return nearby_truth_list


if __name__ == "__main__":
    import pylab as plt

    # Place ground truth on a map.
    maps = map_summaries()
    nearby_truth = place_ground_truth_on_map(maps[0])


