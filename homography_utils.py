"""Utilities for computing homongraphies between images."""
from geo_utils import *
from pixel_position import *

import cv2
from ipdb import set_trace as debug
from osgeo import gdal
import pylab as plt
from skimage.transform import resize


def convert_to_integer(image_array):
    """Convert float array to a uint8 array in range [0, 255]"""
    image_array = image_array / image_array.max() * 255
    return image_array.astype(np.uint8)


def extract_piece_of_map(map_array, col, row, chunk_width=500, chunk_height=500):
    """Extract a chunk of the map array centered around row/col (if possible)."""

    # Characterize the shape of the map.
    map_height, map_width = map_array.shape

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


def match_image_to_map(image_filename, map_filename, make_picture=False):
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
        map_array, col, row, chunk_width=1000, chunk_height=1000
    )

    # Extract a portion of the hi resolution image.
    image_array, image_lower, image_left = extract_piece_of_map(
        image_array, 2000, 1500, 1000, 1000
    )

    # Akshully, let's flip the arrays.
    temp_array = 1 * map_array
    map_array = image_array
    image_array = temp_array

    # Detect the SIFT key points and compute the descriptors.
    sift = cv2.xfeatures2d.SIFT_create()
    keyPoints1, descriptors1 = sift.detectAndCompute(map_array, None)
    keyPoints2, descriptors2 = sift.detectAndCompute(image_array, None)

    # Create brute-force matcher object
    bf = cv2.BFMatcher()

    # Match the descriptors
    matches = bf.knnMatch(descriptors1, descriptors2, k=2)

    # Select the good matches using the ratio test
    good_matches = []

    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    # Apply the homography transformation if we have enough good matches
    MIN_MATCH_COUNT = 10

    if len(good_matches) > MIN_MATCH_COUNT:
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
            **draw_parameters
        )
        plt.ion()
        plt.close("all")
        plt.imshow(result)

    # Return M, the homography, as wel as map and image offsets.
    return M, image_lower, image_left, map_lower, map_left


class GeoReferencer(object):
    """High accuracy georeferencing of image to an orthoreferenced map via homograhy."""

    def __init__(self, image_filename, map_filename):
        """Find the homography mapping between the image and the map."""
        # Compute the image to map honmography (a perspective warp).
        M, image_lower, image_left, map_lower, map_left = match_image_to_map(
            image_filename, map_filename
        )
        self.M, self.image_lower, self.image_left, self.map_lower, self.map_left = (
            M,
            image_lower,
            image_left,
            map_lower,
            map_left,
        )
        self.ortho_obj = gdal.Open(map_filename)
        self.metadata = extract_info(image_filename)
        if M is not None:
            self.valid = True
        else:
            self.valid = False

    def image_shift(self, col, row):
        """Shift pixel into our mapping coordinate system."""
        return col - self.image_left, row - self.image_lower

    def map_shift(self, col, row):
        """Shift pixel into proper map offset coordinate system."""
        col_ = col + self.map_left
        row_ = row + self.map_lower
        return col_, row_

    def pixel_to_latlon(self, col, row):
        """Convert a pixel to lat/lon using computed homography."""
        col_, row_ = self.image_shift(col, row)
        point = np.float32([[col_, row_]]).reshape(-1, 1, 2)
        map_col, map_row = cv2.perspectiveTransform(point, self.M).flatten()
        map_col_, map_row_ = self.map_shift(map_col, map_row)
        lon, lat = pixel_to_coord(self.ortho_obj, map_col_, map_row_)
        return lon, lat

    def image_coord_to_map_coord(self, col, row):
        """Convert a coord in hires image to map coordinate."""
        col_, row_ = self.image_shift(col, row)
        point = np.float32([[col_, row_]]).reshape(-1, 1, 2)
        map_col, map_row = cv2.perspectiveTransform(point, self.M).flatten()
        map_col_, map_row_ = self.map_shift(map_col, map_row)
        return map_col_, map_row_


if __name__ == "__main__":

    path_to_image = ""
    path_to_map = ""
    map_filename = "MinerStreetSmall.tif"
    image_filename = "DJI_0468.JPG"

    homography = match_image_to_map(image_filename, map_filename, make_picture=True)
    gr = GeoReferencer(image_filename, map_filename)
