"""Generate target density maps for specified map."""
from database import *
from models import *
from stores import *
from vessel import Vessel
from skimage.io import imread
from pylab import ion, close, imshow, figure, show, plot



if __name__ == "__main__":
    # Grab a map.
    maps = db.get_maps()
    my_map = maps[4]
    map_id = my_map["map_id"]
    map_model = MapModel(my_map)
    path_to_map = prepend_argos_root(my_map["path_to_geomap"])
    scientific_name = "Frangula alnus"
    print("> Loading map image.")
    map_image = imread(path_to_map)
    height, width, chans = map_image.shape

    ion()
    close("all")
    figure(figsize=(11, 9))
    imshow(map_image)
    map_alpha_beta = []
    probability = []
    for image_path in tqdm(phrag.images.keys()):
        image_dict = phrag.images[image_path]
        map_alpha_beta.extend(image_dict["map_alpha_beta"])
        probability.extend(image_dict["prob"])
    probability = np.array(probability)
    map_alpha_beta = np.array(map_alpha_beta)
    valid_idx = np.nonzero(probability > 0.999)[0]
    # valid_idx = np.flip(np.argsort(probability), 0)
    np.random.shuffle(valid_idx)

    max_idx = int(8e3)
    for idx in valid_idx[:max_idx]:
        alpha, beta = map_alpha_beta[idx]
        plot(beta * width, alpha * height, "r.", alpha=.15)
