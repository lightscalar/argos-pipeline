"""Verify homography-based image registration method."""
from homography_utils import *


if __name__ == "__main__":

    # Here is the thing.
    date = "2018.08.03"
    location = "St Johns Marsh (66)".replace(" ", "_")
    path_to_map = f"maps/{date}/{location}/map_medium.tif"

    DEPOT = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/MNFI/FLIGHTS"
    date = "2018.08.03"
    location = "St Johns Marsh (66)"
    image_number = 763
    path_to_image = f"{DEPOT}/{date}/{location}/DJI_{image_number:04d}.JPG"

    homography = match_image_to_map(path_to_image, path_to_map, make_picture=True)
    # gr = GeoReferencer(path_to_image, path_to_map)

    # map_image = cv2.imread(path_to_map)
    # hires_image = cv2.imread(path_to_image)

    # plt.ion()
    # plt.close('all')
    # plt.figure(100)
    # plt.imshow(map_image)
    # plt.figure(200)
    # plt.imshow(hires_image)
