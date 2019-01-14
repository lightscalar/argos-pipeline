from database import *
from models import *
from vessel import *

from ipdb import set_trace as debug
from pylab import imshow, imread, ion, close
from tqdm import tqdm


def process_map(path_to_map_classification):
    """Convert classifications to the map coordinate system."""
    v = Vessel(path_to_map_classification)
    keys = list(v.images.keys())
    map_id = image_dict["map_id"]
    map_dict = db.get_map(map_id)
    map_model = MapModel(map_dict)
    for key in tqdm(keys):
        image_dict = db.get_image(v.images[key]["image_id"])
        image_model = ImageModel(image_dict)
        X = v.images[key]["X"]
        P = v.images[key]["prob"]
        map_alpha_beta = []
        for x in X:
            lat_lon = image_model.to_lat_lon(*x)
            # Use the large map boundaries!
            map_alpha_beta.append(
                map_model.to_alpha_beta(*lat_lon, boundaries_to_use="map_boundaries")
            )
    v.map_alpha_beta = map_alpha_beta
    v.save()
    print("> Map processed.")


if __name__ == "__main__":
    path_to_annotations = (
        "2018-08-03-st_johns_marsh-66_phragmites_australis_subsp_australis.dat"
    )
    v = Vessel(path_to_annotations)
    keys = list(v.images.keys())
    key = keys[314]
    image_dict = db.get_image(v.images[key]["image_id"])
    map_id = image_dict["map_id"]
    map_dict = db.get_map(map_id)
    map_model = MapModel(map_dict)
    X = v.images[key]["X"]
    P = v.images[key]["prob"]
    path_to_image = prepend_argos_root(image_dict["path_to_image"])
    image = imread(path_to_image)

    for key in tqdm(keys):
        image_dict = db.get_image(v.images[key]["image_id"])
        image_model = ImageModel(image_dict)
        X = v.images[key]["X"]
        P = v.images[key]["prob"]
        map_alpha_beta = []
        for p, x in zip(P, X):
            lat_lon = image_model.to_lat_lon(*x)
            # Use the large map boundaries!
            if p>0.99:
                map_alpha_beta.append(
                    map_model.to_alpha_beta(*lat_lon, boundaries_to_use="map_boundaries")
                )
    v.map_alpha_beta = map_alpha_beta
    v.save()

    # ion()
    # close("all")
    # imshow(image)
    # for p, x in zip(P, X):
    #     if p > 0.9999:
    #         plt.plot(x[1] * 4000, x[0] * 3000, "ro", alpha=p)
