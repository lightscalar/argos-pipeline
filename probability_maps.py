"""Routines for mapping pixels in an image to an invasive species."""
from cnn_bank import *  # imports a NeuralBank instance!
from homography_utils import *
from squares import *
from vessel import Vessel

from glob import glob
from ipdb import set_trace as debug
from matplotlib.pyplot import plot, close, ion, imread
from matplotlib.pyplot import figure, xlim, ylim, xlabel, ylabel, imshow
import matplotlib.pyplot as plt
from matplotlib import ticker, cm
from matplotlib.colors import LogNorm
import numpy as np
from PIL import Image
from scipy.stats import gaussian_kde
from skimage.io import imread
from tqdm import tqdm


def convert_dict_to_map_coords(georeference_obj, probability_dict):
    """Converts a probability dictionary in image coords to map coords."""
    geo, prob_dict = georeference_obj, probability_dict
    map_prob_dict = {}
    for x, p in prob_dict.items():
        map_col, map_row = geo.image_coord_to_map_coord(x[1], x[0])
        map_prob_dict[(map_row, map_col)] = p
    return map_prob_dict


def transparent_cmap(cmap, N=255):
    "Copy colormap and set alpha values"
    mycmap = cmap
    mycmap._init()
    mycmap._lut[:, -1] = np.linspace(0, 0.99, N + 4)
    return mycmap


def plot_density(path_to_image, prob_dict, kde_interval=128, prob_threshold=0.50):
    """Plot species probability density on specified image."""
    X = np.array([list(x) for x, p in prob_dict.items() if p > prob_threshold]).T
    kde = gaussian_kde(X)

    # Use base cmap to create transparent
    mycmap = transparent_cmap(plt.cm.plasma)

    # Open the target image.
    I = imread(path_to_image)
    # I = Image.open(path_to_image)
    p = np.asarray(I).astype("float")
    height, width, chans = I.shape
    rows, cols = np.mgrid[0:height:kde_interval, 0:width:kde_interval]
    rows_ = rows.ravel()
    cols_ = cols.ravel()
    X_ = np.array(list(zip(rows_, cols_))).T
    probability = kde(X_)
    probability -= probability.mean()
    probability /= probability.std()
    plt.close("all")
    fig, ax = plt.subplots(1, 1)
    ax.imshow(I)
    cb = ax.contourf(
        cols,
        rows,
        probability.reshape(cols.shape[0], rows.shape[1]),
        2,
        # levels=np.linspace(1e-6, 1e-5, 2),
        cmap=mycmap,
        antialiased=True,
    )
    fig.subplots_adjust(bottom=0)
    fig.subplots_adjust(top=1)
    fig.subplots_adjust(right=1)
    fig.subplots_adjust(left=0)
    plt.gca().set_axis_off()
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.show()
    return kde


def extract_image_tiles(image, tile_centers, tile_size=128):
    tiles = np.zeros((len(tile_centers), tile_size, tile_size, 3))
    for itr, center in enumerate(tqdm(tile_centers)):
        row = center[0]
        col = center[1]
        tile = np.array(create_rotated_pics(image, row, col, tile_size, 1))
        tiles[itr, :] = tile
    return tiles


def get_tile_centers(image, tile_size):
    """Get the tile centers for tile extraction."""
    width = image.shape[1]
    height = image.shape[0]
    cols, rows = np.meshgrid(
        range(0, width, int(tile_size / 2)), range(0, height, int(tile_size / 2))
    )
    cols = cols.flatten()
    rows = rows.flatten()
    points = list(zip(rows, cols))
    return points


def get_probability_map(image_location, soi_code=28, tile_size=128):
    """Get probabilities for SOIs in specified image."""
    image = plt.imread(image_location)
    points = get_tile_centers(image, tile_size)
    tiles = extract_image_tiles(image, points, tile_size=tile_size)

    # Predicting probabilities...
    print("> Running tiles through the CNN.")
    probabilities = bank.models[soi_code].predict(tiles)
    print("> Complete")
    probabilities = probabilities.flatten()

    # Put probabilities in a dict labeled with tile center as key.
    probs = {}
    for itr, p in enumerate(probabilities):
        probs[points[itr]] = p
    return probs


if __name__ == "__main__":

    # Find an example image.
    DEPOT = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/MNFI/FLIGHTS"
    date = "2018.08.03"
    location = "St Johns Marsh (66)"
    image_number = 232
    path_to_image = f"{DEPOT}/{date}/{location}/DJI_{image_number:04d}.JPG"
    image = plt.imread(path_to_image)
    ion()
    close("all")
    figure(100)
    imshow(image)

    # Get the overall map.
    date = "2018.08.03"
    location = "St Johns Marsh (66)".replace(" ", "_")
    path_to_map = f"maps/{date}/{location}/map_medium.tif"
    geo = GeoReferencer(path_to_image, path_to_map)

    # Compute probabilities
    # prob_dict = get_probability_map(path_to_image, soi_code=14, tile_size=128)
    prob_dict = Vessel("temp.dat").prob_dict

    # Plot density estimate.
    # plot_density(path_to_image, prob_dict, prob_threshold=0.1)

    map_prob_dict = {}
    for x, p in prob_dict.items():
        map_col, map_row = geo.image_coord_to_map_coord(x[1], x[0])
        map_prob_dict[(map_row, map_col)] = p

    plot_density(path_to_map, map_prob_dict, kde_interval=32, prob_threshold=0.1)

    # for p, v in map_prob_dict.items():
    #     if v > 0.10:
    #         plot(p[1], p[0], "r+")
