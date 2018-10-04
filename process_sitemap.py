"""Process an entire sitemap for a targe SOI."""
from probability_maps import *

from glob import glob
from tqdm import tqdm
import os
import re

if __name__ == "__main__":

    # Define target SOI (14 — buckthorn; 28 — phragmites).
    target_soi = 14

    # Get high resolution site images.
    DEPOT = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/MNFI/FLIGHTS"
    date = "2018.08.03"
    location = "St Johns Marsh (66)"
    paths_to_images = glob(f"{DEPOT}/{date}/{location}/DJI*.JPG")

    # Define the sitemap to use.
    map_location = "St Johns Marsh (66)".replace(" ", "_")
    path_to_map = f"maps/{date}/{map_location}/map_medium.tif"

    # Define SOI storage space.
    soi_map_location = f'data/soi_map/{date}/{location.replace(" ", "_")}'
    if not os.path.isdir(soi_map_location):
        os.makedirs(soi_map_location)

    # Process each image.
    for path_to_image in tqdm(paths_to_images):

        # Keep track of image number.
        image_number = int(re.search(r"DJI_(\d+).JPG", path_to_image)[1])

        # Build the GeoReferencer!
        print("> Building GeoReferencer.")
        geo = GeoReferencer(path_to_image, path_to_map)
        print("> Complete.")

        # Compute probabilities.
        prob_dict = get_probability_map(path_to_image, soi_code=14, tile_size=128)
        map_prob_dict = convert_dict_to_map_coords(geo, prob_dict)

        # Store the probabilities on disk.
        store = Vessel(
            filename=f"{soi_map_location}/IMG_{image_number:04d}_SOI_{target_soi:2d}.dat"
        )
        store.prob_dict = map_prob_dict
        store.save()
