"""Utilities for computing homongraphies between images."""
from database import *
from geo_utils import *
from georeferencer import *
from utils import *

import cv2
from ipdb import set_trace as debug
import numpy as np
from osgeo import gdal
import pylab as plt
from skimage.transform import resize


CHUNK_SIZE = 800


def perspective_transform(point, M):
    """Transform point using perspective transformation M."""
    point = np.array(point)
    point = np.hstack((point, 1))
    point_prime = M.dot(point)
    point_prime = point_prime / point_prime[2]
    return point_prime[0:2]


def convert_to_integer(image_array):
    """Convert float array to a uint8 array in range [0, 255]"""
    image_array = image_array / image_array.max() * 255
    return image_array.astype(np.uint8)


def extract_piece_of_map(map_array, col, row, chunk_width=500, chunk_height=500):
    """Extract a chunk of the map array centered around row/col (if possible)."""

    # Characterize the shape of the map.
    map_height, map_width = map_array.shape

    # Make sure we don't grab too much of the image.

    # Find height indices (worry about points near edges of map).
    if row - chunk_height / 2 < 0:
        extra = chunk_height / 2 - row
        lower = 0
        upper = chunk_height / 2 + extra
    elif row + chunk_height / 2 > map_height:
        extra = (row + chunk_height / 2) - map_height
        lower = row - chunk_height / 2 - extra
        upper = map_height
    else:
        lower = row - chunk_height / 2
        upper = row + chunk_height / 2

    # Find width indices.
    if col - chunk_width / 2 < 0:
        extra = chunk_width / 2 - col
        left = 0
        right = col + chunk_width / 2 + extra
    elif col + chunk_width / 2 > map_width:
        extra = col + chunk_width / 2 - map_width
        left = col - chunk_width / 2 - extra
        right = map_width
    else:
        left = col - chunk_width / 2
        right = col + chunk_width / 2
    # Extract the desired region from the full image.
    return map_array[int(lower) : int(upper), int(left) : int(right)], lower, left


def match_image_to_map(
    image_filename, map_filename, make_picture=False, chunk_size=CHUNK_SIZE
):
    """Determine the homography between an image and a map."""

    # Load the images.
    map_array = cv2.imread(map_filename)
    image_array = cv2.imread(image_filename)

    # Convert to grayscale.
    map_array = cv2.cvtColor(map_array, cv2.COLOR_BGR2GRAY)
    image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)

    # Determine approximate lat/lon center of the image; get map georeference data.
    meta_dict = extract_info(image_filename)
    ortho_obj = gdal.Open(map_filename)

    # Extract relevant portion from the map.
    col, row = coord_to_pixel(ortho_obj, meta_dict["img_lon"], meta_dict["img_lat"])
    map_array, map_lower, map_left = extract_piece_of_map(
        map_array, col, row, chunk_width=chunk_size, chunk_height=chunk_size
    )

    # Extract a portion of the hi resolution image.
    image_array, image_lower, image_left = extract_piece_of_map(
        image_array, 2000, 1500, chunk_size, chunk_size
    )

    # Akshully, let's flip the arrays.
    temp_array = np.copy(map_array)
    map_array = image_array
    image_array = temp_array

    # Detect the SIFT key points and compute the descriptors.
    sift = cv2.xfeatures2d.SIFT_create()
    keyPoints1, descriptors1 = sift.detectAndCompute(map_array, None)
    keyPoints2, descriptors2 = sift.detectAndCompute(image_array, None)

    # Create brute-force matcher object
    # bf = cv2.BFMatcher()

    # FLANN parameters
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)  # or pass empty dictionary
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(descriptors1, descriptors2, k=2)

    # Match the descriptors
    try:
        # Select the good matches using the ratio test
        matches = bf.knnMatch(descriptors1, descriptors2, k=2)
        good_matches = []
        for m, n in matches:
            if m.distance < 0.90 * n.distance:
                good_matches.append(m)
    except:
        print("> Match generation failed.")
        good_matches = []
    debug()

    # Apply the homography transformation if we have enough good matches
    MIN_MATCH_COUNT = 5

    if len(good_matches) >= MIN_MATCH_COUNT:
        # Get the good key points positions
        sourcePoints = np.float32(
            [keyPoints1[m.queryIdx].pt for m in good_matches]
        ).reshape(-1, 1, 2)
        destination_points = np.float32(
            [keyPoints2[m.trainIdx].pt for m in good_matches]
        ).reshape(-1, 1, 2)

        # Obtain the homography matrix
        M, mask = cv2.findHomography(
            sourcePoints,
            destination_points,
            method=cv2.RANSAC,
            ransacReprojThreshold=5.0,
        )
        if make_picture:
            matches_mask = mask.ravel().tolist()

            # Apply the perspective transformation to the source image corners
            h, w = map_array.shape
            corners = np.float32(
                [[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]
            ).reshape(-1, 1, 2)
            transformed_corners = cv2.perspectiveTransform(corners, M)

            # Draw a polygon on the second image joining the transformed corners
            image_array = cv2.polylines(
                image_array,
                [np.int32(transformed_corners)],
                True,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
    else:
        print(
            "Not enough matches are found - %d/%d"
            % (len(good_matches), MIN_MATCH_COUNT)
        )
        matches_mask = None
        M = None

    # Draw the matches
    if make_picture:
        # Make a nice picture showing match point correspondence.
        draw_parameters = dict(
            matchColor=(0, 255, 0),
            singlePointColor=None,
            matchesMask=matches_mask,
            flags=2,
        )
        result = cv2.drawMatches(
            map_array,
            keyPoints1,
            image_array,
            keyPoints2,
            good_matches,
            None,
            **draw_parameters,
        )
        plt.ion()
        plt.close("all")
        plt.imshow(result)

    # Return M, the homography, as wel as map and image offsets.
    return M, image_lower, image_left, map_lower, map_left


class GeoReferencer(object):
    """High accuracy georeferencing of image to an orthoreferenced map via homograhy."""

    def __init__(self, image_filename, map_filename, homography=None):
        """Find the homography mapping between the image and the map."""
        # Compute the image to map honmography (a perspective warp).
        if homography is None:
            M, image_lower, image_left, map_lower, map_left = match_image_to_map(
                image_filename, map_filename
            )
        else:
            # We're loading in pre-computed homography mapping.
            M, image_lower, image_left, map_lower, map_left = homography
        # Attach this stuff to the object.
        self.M = M
        self.image_lower = image_lower
        self.image_left = image_left
        self.map_lower = map_lower
        self.map_left = map_left
        self.image_filename = image_filename
        self.map_filename = map_filename
        if self.M is not None:
            self.Minv = np.linalg.inv(self.M)
        self.ortho_obj = gdal.Open(map_filename)
        self.metadata = extract_info(image_filename)
        if M is not None:
            self.valid = True
        else:
            self.valid = False

    def image_shift(self, col, row):
        """Shift pixel into our mapping coordinate system."""
        return col - self.image_left, row - self.image_lower

    def image_unshift(self, col, row):
        """Unshift pixel back to original image coordinate system."""
        return col + self.image_left, row + self.image_lower

    def map_shift(self, col, row):
        """Shift pixel into proper map offset coordinate system."""
        col_ = col + self.map_left
        row_ = row + self.map_lower
        return col_, row_

    def map_unshift(self, col, row):
        """Unshift pixel back to original coordinate system."""
        col_ = col - self.map_left
        row_ = row - self.map_lower
        return col_, row_

    def pixel_to_latlon(self, col, row):
        """Convert an image row/col to lat/lon using computed homography."""
        col_, row_ = self.image_shift(col, row)
        point = np.float32([[col_, row_]]).reshape(-1, 1, 2)
        map_col, map_row = cv2.perspectiveTransform(point, self.M).flatten()
        map_col_, map_row_ = self.map_shift(map_col, map_row)
        lon, lat = pixel_to_coord(self.ortho_obj, map_col_, map_row_)
        return lon, lat

    def image_coord_to_map_coord(self, col, row):
        """Convert a row/col in hires image to map row/col."""
        col_, row_ = self.image_shift(col, row)
        point = np.float32([[col_, row_]]).reshape(-1, 1, 2)
        map_col, map_row = cv2.perspectiveTransform(point, self.M).flatten()
        map_col_, map_row_ = self.map_shift(map_col, map_row)
        return map_col_, map_row_

    def latlon_to_image_coord(self, lat, lon):
        """Map lat/lon to colr/row in the hires image."""
        # This maps lat/lon to position pixel position in high-res image.
        map_col_, map_row_ = coord_to_pixel(self.ortho_obj, lon, lat)
        map_col, map_row = self.map_unshift(map_col_, map_row_)
        col_, row_ = perspective_transform([map_col, map_row], self.Minv)
        col, row = self.image_unshift(col_, row_)
        return col, row


if __name__ == "__main__":
    from glob import glob

    image_list = imagery_collection.find({"map_id": "2018-07-06-st_johns_marsh-66"})
    image_obj = image_list[952]
    path_to_map = prepend_argos_root(image_obj["path_to_map"])
    path_to_image = prepend_argos_root(image_obj["path_to_image"])

    homography = match_image_to_map(path_to_image, path_to_map, make_picture=True)
    # gr = GeoReferencer(path_to_image, path_to_map)
