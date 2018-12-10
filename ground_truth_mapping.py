"""Utilities for mapping ground truth to maps and high-resolution imagery."""
from database import *
from geo_utils import *
from georeferencer import *
from utils import prepend_argos_root, map_summaries

from ipdb import set_trace as debug
from PIL import Image
import pylab as plt


def match_truth_to_target(truth, targets):
    """Augment the truth with scientific name, color code, etc."""
    target_found = False
    for target in targets:
        if truth["code"] in target["codes"]:
            if "H2O" in target["codes"]:
                debug()
            truth["scientific_name"] = target["scientific_name"]
            truth["common_name"] = target["common_name"]
            truth["color_code"] = target["color_code"]
            target_found = True
    if target_found:
        return truth
    else:
        return None


def in_map(row, col, map_rows, map_cols):
    """Determine if ground truth point is inside the specified map."""
    return not (row < 0 or col < 0 or row > map_rows or col > map_cols)


def find_unique_targets(nearby_truth_list):
    """Make a list of all unique ground truth targets present."""
    targets_ = []
    unique_targets = []
    for t in nearby_truth_list:
        if t["scientific_name"] not in targets_:
            targets_.append(t["scientific_name"])
            unique_targets.append(t)
    return unique_targets


def place_ground_truth_on_map(map_obj):
    """Returns list of (row,col) coordinates for placement on small map."""
    # Note this assumes we've imported truth_tree and ground_truth from database.
    path_to_geomap = prepend_argos_root(map_obj["path_to_geomap"])
    path_to_map = prepend_argos_root(map_obj["path_to_map"])

    # Open small map to get size.
    small_map = plt.imread(path_to_map)
    small_rows, small_cols, _ = small_map.shape

    # Open georeference information on the map.
    ds = gdal.Open(path_to_geomap)
    large_rows, large_cols = ds.RasterYSize, ds.RasterXSize

    # Compute large/small conversion factors.
    row_convert = small_rows / large_rows
    col_convert = small_cols / large_cols

    # Find center of the map in lat/lon
    map_lon, map_lat = pixel_to_coord(ds, ds.RasterXSize / 2, ds.RasterYSize / 2)

    # Find all ground truth nearby (nearest k).
    _, nearby_truth = truth_tree.query([[map_lat, map_lon]], k=300)

    # Compile a list of ground truth attached to this map.
    targets = get_targets()
    nearby_truth_list = []
    for truth_idx in nearby_truth[0]:
        tru = ground_truth[truth_idx]
        lat, lon = tru["latlon"]
        col, row = coord_to_pixel(ds, lon, lat)
        small_col = int(col * col_convert)
        small_row = int(row * row_convert)
        if not in_map(row, col, large_rows, large_cols):
            # This point is off the map; all others would be farther away, so break...
            break
        if small_map[small_row, small_col, :].sum() >= 3 * 255:
            # This ground truth point is not on actual imagery...
            continue
        gt = {"col": col * col_convert, "row": row * row_convert, "code": tru["code"]}
        gt = match_truth_to_target(gt, targets)
        if gt is not None:
            nearby_truth_list.append(gt)

    unique_targets_present = find_unique_targets(nearby_truth_list)
    package = {
        "nearby_truth": nearby_truth_list,
        "unique_truth": unique_targets_present,
        "image_rows": small_rows,
        "image_cols": small_col,
    }
    return package


if __name__ == "__main__":
    import pylab as plt

    plt.ion()
    plt.close("all")

    # Place ground truth on a map.
    maps = map_summaries()
    map_idx = 1
    nearby_truth, unique_targets_present = place_ground_truth_on_map(maps[map_idx])
    img = plt.imread(prepend_argos_root(maps[map_idx]["path_to_map"]))
    plt.imshow(img)
    for itr, truth in enumerate(nearby_truth):
        color = truth["color_code"]
        r, c = int(truth["row"]), int(truth["col"])
        plt.plot(
            truth["col"],
            truth["row"],
            "o",
            markersize=5,
            markerfacecolor=color,
            markeredgecolor=color,
        )
    for itr, truth in enumerate(unique_targets_present):
        color = truth["color_code"]
        r, c = int(truth["row"]), int(truth["col"])
        plt.plot(
            truth["col"],
            truth["row"],
            "o",
            markersize=5,
            markerfacecolor=color,
            markeredgecolor=color,
            label=truth["scientific_name"],
        )
    plt.legend()