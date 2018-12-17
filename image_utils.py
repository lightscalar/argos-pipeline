from utils import *

from glob import glob
import re
from tqdm import tqdm


def extract_image_number(path_to_image):
    """Grab the image number from the image name."""
    rgx = r"DJI_(\d+).JPG"
    file_name = path_to_image.split("/")[-1]
    match = re.search(rgx, file_name)
    if match is not None:
        return match[1]


if __name__ == "__main__":

    # Image location.
    maps = map_summaries()
    cmap = maps[0]

    # Get a list of images.
    path_to_images = prepend_argos_root(cmap["path_to_images"])
    images = sorted(glob(f"{path_to_images}/*.JPG"))

    for image in tqdm(images):
        image_number = extract_image_number(image)
        image_id = f"{cmap['map_id']}-IMG_{image_number}"
