from config import *
from database import *
from cnn import *
from models import *
from mcmc import *
import utils

import scipy.spatial as spatial


if __name__ == "__main__":

    # Grab a map.
    maps = db.get_maps()
    map_queue = [
        (8, "Phragmites australis subsp americanus"),  # Negwegon
        (11, "Phragmites australis subsp australis"),  # Wilderness site 2
        (11, "Phragmites australis subsp americanus"),  # Wilderness site 2
        (11, "Typha angustifolia"),  # Wilderness site 2
        (4, "Centaurea stoebe"),  # Warren Dunes site 3
        (14, "Centaurea stoebe"),  # Warren Dunes site 3
        (12, "Centaurea stoebe"),  # Ludington
        (12, "Leymus arenarius"),  # Ludington
        (0, "Centaurea stoebe"),  # Maxton Plains
        (9, "Centaurea stoebe"),  # Maxton Plains
        (8, "Hydrocharis morsus-ranae"),  # Negwegon
    ]

    for map_number, scientific_name in map_queue:

        my_map = maps[map_number]
        map_id = my_map["map_id"]
        map_model = MapModel(my_map)
        # scientific_name = "Centaurea stoebe"
        # scientific_name = "Phragmites australis subsp australis"
        # scientific_name = "Frangula alnus"
        # scientific_name = 'Rhamnus cathartica'
        cnn = CNN(scientific_name, do_load_model=True)

        # Find images.
        path_to_images = f"{prepend_argos_root(my_map['path_to_images'])}/*.JPG"
        images = glob(path_to_images)
        v = Vessel(f"{my_map['map_id']}_{cnn.model_name}.dat")
        if "images" not in v.keys:
            v.images = {}

        images = sorted(images)
        offset = 0  # in case we need to restart; default should be zero
        for itr, path_to_image in enumerate(images[offset:]):
            print(
                f"> Processing {scientific_name} in image {itr+1+offset:04d} of {len(images):04d} for map {map_id}"
            )
            path_to_image = utils.fix_path_to_image(
                path_to_image
            )  # for a few problem images
            image_id = image_location_to_id(path_to_image)
            image_dict = db.get_image(image_id)
            image_model = ImageModel(image_dict)

            # CNN set the image
            cnn.set_image(path_to_image)
            pdf = cnn.predict

            # Scan image.
            alpha = np.linspace(0, 1, 40)
            beta = np.linspace(0, 1, 40)
            image_alpha_beta = []
            target_probability = []
            map_alpha_beta = []
            for a in tqdm(alpha):
                for b in beta:
                    p = cnn.predict(
                        [a + 0.010 * np.random.randn(), b + 0.010 * np.random.randn()]
                    )
                    target_probability.append(p)
                    image_alpha_beta.append([a, b])
                    lat_lon = image_model.to_lat_lon(a, b)
                    map_alpha_beta.append(
                        map_model.to_alpha_beta(
                            *lat_lon, boundaries_to_use="map_boundaries"
                        )
                    )
            # Package up the results.
            v.images[image_id] = {
                "prob": target_probability,
                "X": image_alpha_beta,
                "image_id": image_id,
                "map_id": map_id,
                "map_alpha_beta": map_alpha_beta,
            }
            if np.mod(itr, 25) == 0:
                v.save()
        v.save()
