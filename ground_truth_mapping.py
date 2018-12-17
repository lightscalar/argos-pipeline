"""Utilities for mapping ground truth to maps and high-resolution imagery."""
from database import *
from geo_utils import *
from georeferencer import *
from homography_utils import GeoReferencer
from utils import prepend_argos_root, map_summaries

from ipdb import set_trace as debug
from PIL import Image
import pylab as plt


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


def convert_map_coord_to_lat_lon(col_fraction, row_fraction, map_id):
    """Map specified col/row clicked on web map to lat/lon."""
    map_obj = get_map(map_id)
    geo_rows = map_obj["geo_rows"]
    geo_cols = map_obj["geo_cols"]
    # Scale web map coordinates to georeferenced map.
    col = col_fraction * geo_cols
    row = row_fraction * geo_rows
    ds = gdal.Open(prepend_argos_root(map_obj["path_to_geomap"]))
    # Convert to latitude and longitude.
    map_lon, map_lat = pixel_to_coord(ds, col, row)
    return map_lat, map_lon


def place_ground_truth_on_image(image_obj):
    """Returns a list of (row,col) coordinates for placement on small map."""
    path_to_image = prepend_argos_root(image_obj["path_to_image"])
    path_to_map = prepend_argos_root(image_obj["path_to_map"])
    homography = extract_homography_from_image_object(image_obj)
    gr = GeoReferencer(path_to_image, path_to_map, homography=homography)
    image_lon = image_obj["lon"]
    image_lat = image_obj["lat"]
    _, nearby_truth = global_truth_tree.query([[image_lat, image_lon]], k=100)
    targets = get_targets()
    image = plt.imread(path_to_image)
    image_rows, image_cols, color_channels = image.shape
    nearby_truth_list = []
    for truth_idx in nearby_truth[0]:
        tru = global_ground_truth[truth_idx]
        lat, lon = tru["latlon"]
        col, row = gr.latlon_to_image_coord(lat, lon)
        if not in_map(row, col, image_rows, image_cols):
            break
        gt = {"col": col / image_cols, "row": row / image_rows, "code": tru["code"]}
        gt = match_truth_to_target(gt, targets)
        if gt is not None:
            nearby_truth_list.append(gt)
    # Extract unique ground truth targets.
    unique_targets_present = find_unique_targets(nearby_truth_list)
    unique_targets_present = sorted(
        unique_targets_present, key=lambda x: x["scientific_name"]
    )
    package = {
        "nearby_truth": nearby_truth_list,
        "unique_truth": unique_targets_present,
    }
    return package


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
    _, nearby_truth = global_truth_tree.query([[map_lat, map_lon]], k=300)

    # Compile a list of ground truth attached to this map.
    targets = get_targets()
    nearby_truth_list = []
    for truth_idx in nearby_truth[0]:
        tru = global_ground_truth[truth_idx]
        lat, lon = tru["latlon"]
        col, row = coord_to_pixel(ds, lon, lat)
        small_col = int(col * col_convert)
        small_row = int(row * row_convert)
        if not in_map(row, col, large_rows, large_cols):
            # This point is off the map; all others would be farther away, so break...
            break
        if small_map[small_row, small_col, :].sum() >= 3 * 255:
            # This ground truth point is not on actual imagery, but in white buffer space.
            continue
        gt = {"col": col * col_convert, "row": row * row_convert, "code": tru["code"]}
        gt = match_truth_to_target(gt, targets)
        if gt is not None:
            nearby_truth_list.append(gt)

    unique_targets_present = find_unique_targets(nearby_truth_list)
    unique_targets_present = sorted(
        unique_targets_present, key=lambda x: x["scientific_name"]
    )
    package = {
        "nearby_truth": nearby_truth_list,
        "unique_truth": unique_targets_present,
        "image_rows": small_rows,
        "image_cols": small_cols,
    }
    return package


if __name__ == "__main__":
    import pylab as plt

    plt.ion()
    plt.close("all")

    test_maps = False
    test_imgs = True

    if test_imgs:
        image_list = list(imagery_collection.find({}))
        image_obj = image_list[19]
        path_to_image = prepend_argos_root(image_obj["path_to_image"])
        package = place_ground_truth_on_image(image_obj)
        nearby_truth = package["nearby_truth"]
        unique_truth = package["unique_truth"]
        img = plt.imread(path_to_image)
        plt.imshow(img)
        for itr, truth in enumerate(nearby_truth):
            color = truth["color_code"]
            r, c = int(truth["row"] * img.shape[0]), int(truth["col"] * img.shape[1])
            plt.plot(
                c, r, "o", markersize=5, markerfacecolor=color, markeredgecolor=color
            )
        for itr, truth in enumerate(unique_truth):
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

    if test_maps:
        # Place ground truth on a map.
        maps = map_summaries()
        map_idx = 1
        truths = place_ground_truth_on_map(maps[map_idx])
        nearby_truth = truths["nearby_truth"]
        unique_truth = truths["unique_truth"]
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
        for itr, truth in enumerate(unique_truth):
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
