"""Generate target density maps for specified map."""
from database import *
from models import *
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
    v = Vessel("2018-08-03-st_johns_marsh-66_phragmites_australis_subsp_australis.dat")
    map_alpha_beta = v.map_alpha_beta
    map_image = imread(path_to_map)
    height, width, chans = map_image.shape

    ion()
    close("all")
    figure(figsize=(11, 9))
    imshow(map_image)

    for alpha, beta in map_alpha_beta:
        plot(beta * width, alpha * height, "ro", alpha=0.6, markersize=5)
