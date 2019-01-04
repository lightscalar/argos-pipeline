"""Utilities for working with geo-rectified imagery."""
from vessel import Vessel

from exiftool import ExifTool
import geomag
from geopy.distance import distance
from ipdb import set_trace as debug
import numpy as np


def distance_on_earth(a, b):
    """Find the distance (in meters) between two points on the Earth."""
    return distance(a, b).meters


def calculate_meters_per_pixel(fov, altitude, diagonal_length):
    """Compute meters_per_pixel for the image."""
    fov_over_2 = fov / 2 * np.pi / 180
    diag_over_2 = diagonal_length / 2
    half_diag_in_meters = altitude * np.tan(fov_over_2)
    half_diag_in_pixels = diagonal_length / 2
    return half_diag_in_meters / half_diag_in_pixels


def calculate_image_radius_in_meters(exif_obj):
    """Calculate the radius of the image (as measured along diagonal."""
    d = exif_obj
    diagonal_length_in_pixels = np.sqrt(d["img_width"] ** 2 + d["img_height"] ** 2)
    meters_per_pixel = calculate_meters_per_pixel(
        d["field_of_view"], d["relative_altitude"], diagonal_length_in_pixels
    )
    return meters_per_pixel * diagonal_length_in_pixels / 2


def unit_vectors(exif_obj):
    """Compute east and north unit vectors given the camera yaw."""
    camera_yaw = exif_obj["camera_yaw"]
    lat, lon = exif_obj["img_lat"], exif_obj["img_lon"]
    declination = geomag.declination(lat, lon)
    camera_yaw += declination  # compensate for magnetic variation
    alpha = camera_yaw * np.pi / 180
    n = [-np.cos(alpha), -np.sin(alpha)]
    e = [-np.sin(alpha), np.cos(alpha)]
    return np.array(n), np.array(e)


def extract_info(image_file):
    """Extract necessary data from metadata dictionary."""
    image_file = image_file.replace("'", "")
    with ExifTool() as et:
        metadata = et.get_metadata(image_file)
    data = {}
    data["field_of_view"] = metadata["Composite:FOV"]
    data["camera_yaw"] = metadata["MakerNotes:CameraYaw"]
    data["relative_altitude"] = float(metadata["XMP:RelativeAltitude"])
    data["img_lat"] = metadata["Composite:GPSLatitude"]
    data["img_lon"] = metadata["Composite:GPSLongitude"]
    data["img_width"] = metadata["File:ImageWidth"]
    data["img_height"] = metadata["File:ImageHeight"]
    data["date_time"] = metadata["EXIF:DateTimeOriginal"]
    return data


def pixel_to_lat_lon(row, col, image_file=None, exif_info=None):
    """Convert given pixel position to lat/lon."""
    if exif_info:
        d = exif_info
    else:
        d = extract_info(image_file)
    diagonal_length_in_pixels = np.sqrt(d["img_width"] ** 2 + d["img_height"] ** 2)
    meters_per_pixel = calculate_meters_per_pixel(
        d["field_of_view"], d["relative_altitude"], diagonal_length_in_pixels
    )
    # Compute the unit vectors in the north and east directions.
    # Find dispacement in those directions, given specfied latitude/longitude.
    n, e = unit_vectors(d)
    pixel_vector = np.array([row - d["img_height"] / 2, col - d["img_width"] / 2])
    dn_in_meters = np.dot(pixel_vector, n) * meters_per_pixel
    de_in_meters = np.dot(pixel_vector, e) * meters_per_pixel

    pos = np.array([d["img_lat"], d["img_lon"]])
    meters_per_degree_lat = distance_on_earth(pos, pos + [1, 0])
    meters_per_degree_lon = distance_on_earth(pos, pos + [0, 1])
    dn_in_degrees = dn_in_meters / meters_per_degree_lat
    de_in_degrees = de_in_meters / meters_per_degree_lon

    lat = d["img_lat"] + dn_in_degrees
    lon = d["img_lon"] + de_in_degrees
    return lat, lon


def alpha_beta_to_lat_lon(alpha, beta, image_file=None, exif_info=None):
    """Convert given pixel position to lat/lon."""
    if exif_info:
        d = exif_info
    else:
        d = extract_info(image_file)
    row = d["img_height"] * alpha
    col = d["img_width"] * beta
    diagonal_length_in_pixels = np.sqrt(d["img_width"] ** 2 + d["img_height"] ** 2)
    meters_per_pixel = calculate_meters_per_pixel(
        d["field_of_view"], d["relative_altitude"], diagonal_length_in_pixels
    )
    # Compute the unit vectors in the north and east directions.
    # Find dispacement in those directions, given specfied latitude/longitude.
    n, e = unit_vectors(d)
    pixel_vector = np.array([row - d["img_height"] / 2, col - d["img_width"] / 2])
    dn_in_meters = np.dot(pixel_vector, n) * meters_per_pixel
    de_in_meters = np.dot(pixel_vector, e) * meters_per_pixel

    pos = np.array([d["img_lat"], d["img_lon"]])
    meters_per_degree_lat = distance_on_earth(pos, pos + [1, 0])
    meters_per_degree_lon = distance_on_earth(pos, pos + [0, 1])
    dn_in_degrees = dn_in_meters / meters_per_degree_lat
    de_in_degrees = de_in_meters / meters_per_degree_lon

    lat = d["img_lat"] + dn_in_degrees
    lon = d["img_lon"] + de_in_degrees
    return lat, lon


def lat_lon_to_alpha_beta(lat, lon, image_file=None, exif_info=None):
    """Convert from lat/lon to unit position within the image."""
    if exif_info:
        d = exif_info
    else:
        d = extract_info(image_file)
    diagonal_length_in_pixels = np.sqrt(d["img_width"] ** 2 + d["img_height"] ** 2)
    meters_per_pixel = calculate_meters_per_pixel(
        d["field_of_view"], d["relative_altitude"], diagonal_length_in_pixels
    )
    # Compute the unit vectors in the north and east directions.
    # Find dispacement in those directions, given specfied latitude/longitude.
    n, e = unit_vectors(d)
    pos = np.array([d["img_lat"], d["img_lon"]])
    meters_per_degree_lat = distance_on_earth(pos - [0.5, 0], pos + [0.5, 0])
    meters_per_degree_lon = distance_on_earth(pos - [0, 0.5], pos + [0, 0.5])
    dn_in_meters = (lat - d["img_lat"]) * meters_per_degree_lat
    de_in_meters = (lon - d["img_lon"]) * meters_per_degree_lon

    # Compute delta in N/S and E/W direction.
    dn_in_pixels = dn_in_meters / meters_per_pixel
    de_in_pixels = de_in_meters / meters_per_pixel

    # Projected position is location relative to center of image.
    ctr_position = np.array([d["img_height"] / 2, d["img_width"] / 2])
    target_position = ctr_position + (dn_in_pixels * n + de_in_pixels * e)
    alpha = target_position[0] / d["img_height"]
    beta = target_position[1] / d["img_width"]
    return alpha, beta


def project_on_image(lat, lon, image_file):
    """Project given lat and lon onto coordinate system of the specified image."""
    d = extract_info(image_file)
    diagonal_length_in_pixels = np.sqrt(d["img_width"] ** 2 + d["img_height"] ** 2)
    meters_per_pixel = calculate_meters_per_pixel(
        d["field_of_view"], d["relative_altitude"], diagonal_length_in_pixels
    )
    # Compute the unit vectors in the north and east directions.
    # Find dispacement in those directions, given specfied latitude/longitude.
    n, e = unit_vectors(d)
    pos = np.array([d["img_lat"], d["img_lon"]])
    meters_per_degree_lat = distance_on_earth(pos - [0.5, 0], pos + [0.5, 0])
    meters_per_degree_lon = distance_on_earth(pos - [0, 0.5], pos + [0, 0.5])
    dn_in_meters = (lat - d["img_lat"]) * meters_per_degree_lat
    de_in_meters = (lon - d["img_lon"]) * meters_per_degree_lon

    # Compute delta in N/S and E/W direction.
    dn_in_pixels = dn_in_meters / meters_per_pixel
    de_in_pixels = de_in_meters / meters_per_pixel

    # Projected position is location relative to center of image.
    ctr_position = np.array([d["img_height"] / 2, d["img_width"] / 2])
    target_position = ctr_position + (dn_in_pixels * n + de_in_pixels * e)
    return target_position


def in_image(location, image_file: str):
    """Determine if a latitude/longitude coordinate is contained within specified image."""
    lat, lon = location[0], location[1]
    image_file = image_file.replace("'", "")
    row, col = project_on_image(lat, lon, image_file)
    row_bounds = (row > 0) * (row < 3000)
    col_bounds = (col > 0) * (col < 4000)
    return row_bounds * col_bounds


if __name__ == "__main__":
    from database import *
    from models import *
    from glob import glob
    import pylab as plt

    # Try to map a given image back on to a map.
    maps = db.get_maps()
    path_to_images = maps[3]["path_to_images"]
    path_to_images = prepend_argos_root(path_to_images)
    images = glob(f"{path_to_images}/*.JPG")
    images = sorted(images)
    mapm = MapModel(maps[3])
    map_image = plt.imread(prepend_argos_root(mapm.path_to_map))

    def plot_image(image):
        ul_lat, ul_lon = pixel_to_lat_lon(0, 0, image)
        ll_lat, ll_lon = pixel_to_lat_lon(3000, 0, image)
        ur_lat, ur_lon = pixel_to_lat_lon(0, 4000, image)
        lr_lat, lr_lon = pixel_to_lat_lon(3000, 4000, image)

        ul_alpha, ul_beta = mapm.to_alpha_beta(ul_lat, ul_lon)
        ll_alpha, ll_beta = mapm.to_alpha_beta(ll_lat, ll_lon)
        ur_alpha, ur_beta = mapm.to_alpha_beta(ur_lat, ur_lon)
        lr_alpha, lr_beta = mapm.to_alpha_beta(lr_lat, lr_lon)

        map_height, map_width, color_chans = map_image.shape
        mh, mw = map_height, map_width

        def make_line(x1, y1, x2, y2):
            """Create a line between two points."""
            start = np.array([x1, y1])
            stop = np.array([x2, y2])
            alpha = np.linspace(0, 1, 100)
            points = []
            for a in alpha:
                points.append(start * (1 - a) + stop * a)
            return np.array(points)

        ur_ul_line = make_line(ur_beta * mw, ur_alpha * mh, ul_beta * mw, ul_alpha * mh)
        ul_ll_line = make_line(ul_beta * mw, ul_alpha * mh, ll_beta * mw, ll_alpha * mh)
        ll_lr_line = make_line(ll_beta * mw, ll_alpha * mh, lr_beta * mw, lr_alpha * mh)
        lr_ur_line = make_line(lr_beta * mw, lr_alpha * mh, ur_beta * mw, ur_alpha * mh)
        plt.plot(ur_ul_line[:, 0], ur_ul_line[:, 1], color="#ffcc33")
        plt.plot(ul_ll_line[:, 0], ul_ll_line[:, 1], color="#ffcc33")
        plt.plot(ll_lr_line[:, 0], ll_lr_line[:, 1], color="#ffcc33")
        plt.plot(lr_ur_line[:, 0], lr_ur_line[:, 1], color="#ffcc33")
        plt.plot(ul_beta * map_width, ul_alpha * map_height, "ro")

    plt.ion()
    plt.close("all")
    plt.imshow(map_image)
    # image 668 (Aug.03.2018 st_johns_marsh) gives good orientation info.
    start_image = 667
    for image in images[start_image : start_image + 1]:
        plot_image(image)

    plt.figure()
    img = plt.imread(images[start_image])
    plt.imshow(img)
