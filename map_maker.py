from config import *
from database import *
from cnn import *
from models import *
from mcmc import *
import scipy.spatial as spatial


if __name__ == "__main__":

    # Grab a map.
    maps = db.get_maps()
    my_map = maps[4]
    map_id = my_map["map_id"]
    map_model = MapModel(my_map)
    scientific_name = "Frangula alnus"
    # scientific_name = "Phragmites australis subsp australis"
    cnn = CNN(scientific_name, do_load_model=True)

    # Find images.
    path_to_images = f"{prepend_argos_root(my_map['path_to_images'])}/*.JPG"
    images = glob(path_to_images)
    v = Vessel(f"{my_map['map_id']}_{cnn.model_name}.dat")
    if "images" not in v.keys:
        v.images = {}

    images = sorted(images)
    for itr, image in enumerate(images):
        print(f"> Processing image {itr+1:04d} of {len(images):04d}")
        image_id = image_location_to_id(image)
        image_dict = db.get_image(image_id)
        image_model = ImageModel(image_dict)

        # CNN set the image
        cnn.set_image(image)
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
        v.save()
