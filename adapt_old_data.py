from vessel import *

from ipdb import set_trace as debug
import re


DATE_REGEX = r"(\d+).(\d+).(\d+)"
SITE_REGEX = r"(\w+\()(\d+)"
SITE_NAME_MAPPING = {
    "st_johns_marsh": "st_johns_marsh",
    "algonac_state_park": "algonac_st_park",
    "wilderness_site_1": "wilderness_site_1",
    "warren_dunes_site_3": "warren_dunes_site_3",
    "warren_dunes_floral_lane": "warren_dunes_floral_lane",
    "drummond_island": "drummond_island_alvar",
    "negwegon": "negwegon_site_1",
    "drummond_island_site_1": "drummond_island_alvar",
    "negwegon_site_1": "negwegon_site_1",
    "wilderness_site_2": "wilderness_site_2",
}
skip_sites = [
    "obliques",
    "ludiongton_site_1b",
    "elberta_site_1",
    "warren_dunes_site_2",
    "ludington_site_1",
    "warren_dunes_site_1",
    "squaw_bay",
    "negwegon_site_2",
    "fish_point",
    "elberta",
    "elberta_tiny",
    "point_betsie",
    "drummond_island_site_2",
    "st_vitals_bay",
    "munuscong_site_2",
    "wilderness_site_2_quick",
]


def image_path_to_image_id(path_to_image):
    """Convert the path to an image to a proper image_id in the new style."""
    path_list = path_to_image.split("/")
    date = path_list[-3]
    site = path_list[-2]
    image_number = path_list[-1].replace(".JPG", "")
    # Extract name of site.
    try:
        site_name = re.search(r"([\w\.\s]+)", site)[1].strip()
        site_name = site_name.replace(".", "").replace(" ", "_").lower()
        site_name = SITE_NAME_MAPPING[site_name]
    except:
        print("Cannot extract site name.")
        if site_name not in skip_sites:
            print(site_name)
            debug()
        else:
            return None
    # Extract altitude.
    try:
        altitude = re.search(r"\((\d+)\)", site)[1]
    except:
        print("Cannot extract site altitude.")
        return None
    # Extract date.
    match = re.search(DATE_REGEX, date)
    if match is None:
        print("Cannot extract data.")
        return None
    else:
        year = match[1]
        month = match[2]
        day = match[3]
    image_id = f"{year}-{month}-{day}-{site_name}-{altitude}-{image_number.replace('DJI', 'IMG')}"
    return image_id


def convert_old_annotation(annotation_dict):
    """Convert old-style annotation to the new format."""
    path_to_image = annotation_dict["local_location"]
    image_id = image_path_to_image_id(path_to_image)
    annotations = []
    for annot in annotation["annotations"]:
        if "plant" not in annot.keys():
            print("No plant name? Quoi?")
            continue
        alpha = annot["row"] / annot["imageHeight"]
        beta = annot["col"] / annot["imageWidth"]
        alpha_ = int(1e4 * alpha)
        beta_ = int(1e4 * beta)
        annotation_id = f"{image_id}-{alpha_:04d}-{beta_:04d}"
        scientific_name = annot["plant"]
        annot_dict = {
            "alpha": alpha,
            "beta": beta,
            "annotation_id": annotation_id,
            "element_id": f"{alpha_:04d}-{beta_:04d}",
            "scientific_name": scientific_name,
            "image_id": image_id,
        }
        annotations.append(annot_dict)
    return annotations


if __name__ == "__main__":

    # Load the old-style annotations.
    path_to_annotations = "data/annotated_images.dat"
    v = Vessel(path_to_annotations)

    # Convert to new-style image_id.
    new_annotations = []
    for annotation in v.annotated_images:
        new_annotations.extend(convert_old_annotation(annotation))

    # Save these converted annotations for import into appropriate database.
    v_transform = Vessel("data/2019.01.07_legacy_annotations.dat")
    v_transform.annotations = new_annotations
    v_transform.save()
