"""Build tiles for a one vs many CNN classifier."""
from config import *
from geo_utils import extract_info
from squares import *
from vessel import Vessel

from datetime import datetime
from glob import glob
from ipdb import set_trace as debug
from osgeo import gdal, osr
import pylab as plt
from skimage.io import imread
import shutil
import re
from tqdm import tqdm


try:
    maps = Vessel("data/maps.dat")
    id_to_plant = maps.id_to_plant
    plant_to_id = maps.plant_to_id
except:
    pass


def make_image_name(image_object):
    """Make a reasonable image name to hold all the annotations for that image."""
    date = image_object["date"]
    flight = image_object["flight_name"].replace(" ", "_").replace("'", "")
    image_file = image_object["image_loc"].split("/")[-1].replace(" ", "_")
    return f"{date}-{flight}-{image_file}.dat"


def create_label_maps(path_to_annotations, path_to_maps):
    """Find species to integer (and inverse) maps."""
    # Find all unique species.
    v = Vessel(path_to_annotations)
    unique_species = set({})
    for img in v.annotated_images:
        for annotation in img["annotations"]:
            if "plant" not in annotation.keys():
                continue
            unique_species.add(annotation["plant"])
    unique_species = sorted(list(unique_species))

    # Build label maps.
    label_map = {}
    label_map_inverse = {}
    for itr, plant_name in enumerate(unique_species):
        label_map_inverse[plant_name] = itr
        label_map[itr] = plant_name

    maps = Vessel(path_to_maps)
    maps.plant_to_id = label_map_inverse
    maps.id_to_plant = label_map
    maps.save()


def find_target_images(target_species, images):
    """Find the target species in the annotated image collection."""
    maps = Vessel("data/label_maps.dat")
    label_map_inverse = maps.label_map_inverse
    target_images = []
    for img in images:
        codes = [
            label_map_inverse[a["plant"]]
            for a in img["annotations"]
            if "plant" in a.keys()
        ]
        if target_species in codes:
            target_images.append(img)
    return target_images


def extract_tiles_from_image(
    image,
    annotations,
    tile_size=128,
    target_species=None,
    include_target=True,
    max_nb_tiles=2000,
):
    """Pull the given annotation from the image."""
    labels = []
    tiles = np.array([])
    for annotation in annotations:
        if "plant" not in annotation.keys():
            continue
        if include_target:
            if plant_to_id[annotation["plant"]] != target_species:
                continue
        else:  # require this species
            if plant_to_id[annotation["plant"]] == target_species:
                continue

        # Extract tiles, if we're still here.
        if target_species < 0:
            debug()
        col, row = annotation["col"], annotation["row"]
        col_, row_ = (
            col * 4000 / annotation["imageWidth"],
            row * 3000 / annotation["imageHeight"],
        )
        tiles_ = np.array(create_rotated_pics(image, row_, col_, tile_size, 25))
        if tiles.shape[0] > 0:
            tiles = np.vstack((tiles, tiles_))
        else:
            tiles = tiles_
        # Only return max numbers of tiles.
        if tiles.shape[0] > max_nb_tiles:
            break
    return tiles


def add_to_array(X, X_to_add, max_size):
    """Append array to existing array OR create if necessary."""
    if X_to_add.shape[0] == 0:
        return X
    if X.shape[0] > 0:
        X = np.vstack((X, X_to_add))
    else:
        X = X_to_add
    if X.shape[0] >= max_size:
        X = X[:max_size, :]
    return X


def extract_balanced_tiles(
    path_to_annotations, target_species, tile_size=128, tiles_per_class=2000
):
    """Extract equal numbers of target species tiles and tiles from randomly selected species."""
    print("> Extracting tiles.")
    maps = Vessel("data/label_maps.dat")
    data = Vessel(path_to_annotations)
    images = data.annotated_images
    nb_images = len(images)
    target_images = find_target_images(target_species, images)
    nb_target_images = len(target_images)
    y_target = np.ones(tiles_per_class)
    y_other = np.zeros(tiles_per_class)
    X_target = np.array([])
    X_other = np.array([])
    # Grab data from the target set.
    task_complete = False
    while not task_complete:
        image_number = np.random.choice(nb_target_images)
        image = imread(target_images[image_number]["local_location"])[0]
        annotations = target_images[image_number]["annotations"]
        tiles = extract_tiles_from_image(
            image,
            annotations,
            tile_size=tile_size,
            target_species=target_species,
            max_nb_tiles=tiles_per_class,
        )
        X_target = add_to_array(X_target, tiles, tiles_per_class)
        task_complete = X_target.shape[0] == tiles_per_class

    # Grab data from random "other" species.
    task_complete = False
    while not task_complete:
        image_number = np.random.choice(nb_images)
        image = imread(images[image_number]["local_location"])[0]
        annotations = images[image_number]["annotations"]
        tiles = extract_tiles_from_image(
            image,
            annotations,
            tile_size=tile_size,
            target_species=target_species,
            include_target=False,
            max_nb_tiles=tiles_per_class,
        )
        X_other = add_to_array(X_other, tiles, tiles_per_class)
        task_complete = X_other.shape[0] == tiles_per_class

    idx = np.arange(tiles_per_class * 2)
    np.random.shuffle(idx)
    X = np.vstack((X_target, X_other))
    y = np.hstack((y_target, y_other))
    print("> Extraction complete.")
    return X[idx, :], y[idx].astype(int)


def map_summaries():
    """Return the map summary information."""
    flights = []
    years = glob(f"{ARGOS_ROOT}/*")
    maps = []
    for year in years:
        months = sorted(glob(f"{year}/*"))
        # print(year)
        # print(months)
        for month in months:
            days = sorted(glob(f"{month}/*"))
            for day in days:
                sites = sorted(glob(f"{day}/*"))
                for site in sites:
                    altitudes = sorted(glob(f"{site}/*"))
                    for altitude in altitudes:
                        if altitude.split("/")[-1] != "obliques":
                            images = sorted(glob(f"{altitude}/images/*.JPG"))
                            images.sort(key=os.path.getmtime)
                            nb_images = len(images)
                            if nb_images > 0:  # if no images, just why?
                                first_meta = extract_info(images[0])
                                last_meta = extract_info(images[-1])
                                start = first_meta["date_time"]
                                try:
                                    datetime_obj = datetime.strptime(
                                        start, "%Y:%m:%d %H:%M:%S"
                                    )
                                except:
                                    debug()
                                datetime_str = datetime_obj.strftime("%d %b %Y")
                                smalldate = datetime_obj.strftime("%Y-%m-%d")
                                time_str = datetime_obj.strftime("%I-%M%p")
                                alt = altitude.split("/")[-1]
                                sitename = site.split("/")[-1]
                                year_ = year.split("/")[-1]
                                month_ = month.split("/")[-1]
                                day_ = day.split("/")[-1]
                                end = last_meta["date_time"]
                                path_to_map = f"{altitude}/maps/map_small.jpg"
                                path_to_geomap = f"{altitude}/maps/map.tif"
                                path_to_images = f"{altitude}/images"
                                map_id = f"{year_}-{month_}-{day_}-{sitename}-{alt}"

                                # Get map sizes.
                                if len(glob(path_to_geomap)) == 0:
                                    continue
                                ds = gdal.Open(path_to_geomap)
                                geo_rows = ds.RasterYSize
                                geo_cols = ds.RasterXSize
                                small_map = plt.imread(path_to_map)
                                small_rows, small_cols, _ = small_map.shape
                            else:
                                continue  # No images? Don't return this map.
                            if len(glob(f"{altitude}/maps/map.tif")) > 0:
                                maps.append(
                                    {
                                        "map_id": map_id,
                                        "year": year_,
                                        "month": month_,
                                        "day": day_,
                                        "site": sitename,
                                        "altitude": alt,
                                        "nb_images": nb_images,
                                        "geo_rows": geo_rows,
                                        "geo_cols": geo_cols,
                                        "small_rows": small_rows,
                                        "small_cols": small_cols,
                                        "lat": f"{first_meta['img_lat']:.4f}",
                                        "lon": f"{first_meta['img_lon']:.4f}",
                                        "start": start,
                                        "end": end,
                                        "time": time_str.replace("-", ":"),
                                        "datetime": datetime_str,
                                        "path_to_geomap": "/".join(
                                            path_to_geomap.split("/")[-7:]
                                        ),
                                        "path_to_map": "/".join(
                                            path_to_map.split("/")[-7:]
                                        ),
                                        "path_to_images": "/".join(
                                            path_to_images.split("/")[-6:]
                                        ),
                                    }
                                )
    maps = sorted(maps, key=lambda x: x["start"])
    return maps


def parse_image_id(image_id):
    """Extract info from the image ID."""
    image_id_list = image_id.split("-")
    map_id = "-".join(image_id_list[:-1])
    year = image_id_list[0]
    month = image_id_list[1]
    day = image_id_list[2]
    site = image_id_list[3]
    altitude = image_id_list[4]
    image_number = image_id_list[5]
    path_to_map_root = "/".join(image_id_list[:-1])
    path_to_image = f"{path_to_map_root}/images/{image_number}.JPG".replace(
        "IMG", "DJI"
    )
    return {
        "image_id": image_id,
        "error": False,
        "map_id": map_id,
        "year": int(year),
        "month": int(month),
        "day": int(day),
        "site": site,
        "altitude": int(altitude),
        "image_number": image_number,
        "path_to_image": path_to_image,
        "path_to_map": f"{path_to_map_root}/maps/map.tif",
    }


def parse_map_id(map_id):
    """Extract map location/etc from a map id."""
    rgx = r"(\d+)-(\d+)-(\d+)-(\w+)-(\d+)"
    match = re.search(rgx, map_id)
    if match is not None:
        year = match[1]
        month = match[2]
        day = match[3]
        site = match[4]
        altitude = match[5]
        return {
            "error": False,
            "year": year,
            "month": month,
            "day": day,
            "site": site,
            "altitude": altitude,
        }
    else:
        return {"error": "Cannot parse given map ID."}


def fix_image_filenames(path_to_images):
    """Let's fix the filenames of images for folders with more than 1000 images."""
    images = glob(f"{path_to_images}/*.JPG")
    rgx = r"(DJI_)(\d+)"
    for img in images:
        fn = img.split("/")[-1]
        if len(fn) > 12:
            scan = re.search(rgx, fn)
            if scan is not None:
                new_image_number = 1000 + int(scan[2])
                new_image_name = f"DJI_{new_image_number:04d}.JPG"
                path_to_new_image = f"{path_to_images}/{new_image_name}"
                shutil.move(img, path_to_new_image)


def prepend_argos_root(path):
    """Augments a relative path with absolute path to ARGOS root."""
    return f"{ARGOS_ROOT}/{path}"


def extract_homography_from_image_object(image_obj):
    """Get the transformation matrix and offsets into a tuple"""
    M = np.array(image_obj["geo_M"])
    if M.shape[0] == 0:
        M = None
    image_lower = image_obj["geo_image_lower"]
    image_left = image_obj["geo_image_left"]
    map_lower = image_obj["geo_map_lower"]
    map_left = image_obj["geo_map_left"]
    return (M, image_lower, image_left, map_lower, map_left)


if __name__ == "__main__":

    # DEPOT = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/MNFI/FLIGHTS"
    # date = "2018.08.03"
    # location = "St Johns Marsh (66)"
    # location = "Algonac State Park (66)"
    # path_to_images = f"{DEPOT}/{date}/{location}"
    # fix_image_filenames(path_to_images)
    maps = map_summaries()

    # X, y = extract_balanced_tiles("data/annotated_images.dat", 28)

    # create_maps = False
    # if create_maps:
    #     create_label_maps("data/annotated_images.dat")
    # else:
    #     maps = Vessel("data/label_maps.dat")

    # # Now extract tiles on an image by image basis.
    # tile_size = 128
    # for img_obj in v.annotated_images:
    #     filename = make_image_name(img_obj)
    #     path_to_tile_file = f"data/tiles/{filename}"
    #     td = Vessel(path_to_tile_file)
    #     td.tiles = np.array([])
    #     td.labels = []
    #     img = imread(img_obj["local_location"])[0]
    #     for annotation in tqdm(img_obj["annotations"]):
    #         if "plant" not in annotation.keys():
    #             continue
    #         plant_name = annotation["plant"]
    #         col, row = annotation["col"], annotation["row"]
    #         col_, row_ = (
    #             col * 4000 / annotation["imageWidth"],
    #             row * 3000 / annotation["imageHeight"],
    #         )
    #         tiles = np.array(create_rotated_pics(img, row_, col_, tile_size, 10))
    #         if td.tiles.shape[0] > 0:
    #             td.tiles = np.vstack((td.tiles, tiles))
    #         else:
    #             td.tiles = tiles
    #         for k in range(tiles.shape[0]):
    #             td.labels.append(label_map_inverse[plant_name])
    #     debug()
    #     td.save()
