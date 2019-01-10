from config import *
from database import *
from cnn import *
from mcmc import *
import scipy.spatial as spatial


if __name__ == "__main__":

    # Grab a map.
    maps = db.get_maps()
    my_map = maps[4]
    map_id = my_map["map_id"]
    scientific_name = "Frangula alnus"
    scientific_name = "Phragmites australis subsp australis"
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

        # CNN set the image
        cnn.set_image(image)
        pdf = cnn.predict

        # Scan image.
        MCMC = False
        if not MCMC:
            alpha = np.linspace(0, 1, 40)
            beta = np.linspace(0, 1, 40)
            X = []
            P = []
            for a in tqdm(alpha):
                for b in beta:
                    p = cnn.predict(
                        [a + 0.005 * np.random.randn(), b + 0.005 * np.random.randn()]
                    )
                    P.append(p)
                    X.append([a, b])
            v.images[image_id] = {
                "prob": P,
                "X": X,
                "image_id": image_id,
                "map_id": map_id,
            }
            v.save()
        else:
            X = []
            P = []
            for k in range(10):
                X_, P_ = mcmc(pdf, nb_iter=50)
                X.extend(X_)
                P.extend(P_)
            X_, P_ = X, P
