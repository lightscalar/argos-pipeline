"""Generate target density maps for specified map."""
from database import *
from models import *
from stores import *
from vessel import Vessel

from fastkde import fastKDE
import numpy as np
from skimage.io import imread
from pylab import ion, close, imshow, figure, show, plot
from tqdm import tqdm


class HeatMap:
    """Generate density and point maps."""

    def __init__(self, map_dict, map_data):
        """Load map image, extract points."""
        self.map_dict = map_dict
        self.map_data = map_data
        self.extract_points()
        path_to_map = prepend_argos_root(map_dict["path_to_geomap"])
        # Load the map image.
        self.map_image = imread(path_to_map)
        self.height, self.width, chans = self.map_image.shape

    def extract_points(self):
        """Extract likely target positions from map data."""
        map_data = self.map_data
        map_alpha_beta = []
        probability = []
        for image_path in map_data.images.keys():
            image_dict = map_data.images[image_path]
            map_alpha_beta.extend(image_dict["map_alpha_beta"])
            probability.extend(image_dict["prob"])
        probability = np.array(probability)
        map_alpha_beta = np.array(map_alpha_beta)
        valid_idx = np.nonzero(probability > 0.999)[0]
        np.random.shuffle(valid_idx)
        self.map_alpha_beta = map_alpha_beta
        self.valid_idx = valid_idx

    def get_points(self, max_number=8000):
        """Return row/col points in map coordinate system."""
        points = []
        rows = []
        cols = []
        for idx in self.valid_idx[:max_number]:
            alpha, beta = self.map_alpha_beta[idx]
            row, col = alpha * self.height, beta * self.width
            rows.append(row)
            cols.append(col)
        return np.array(rows), np.array(cols)

    def plot_density(self, max_number=9000):
        """Plot the density using kernel densty estimates (KDEs)."""
        spacing = 2049
        # Use base cmap to create transparent.
        mycmap = transparent_cmap(plt.cm.plasma)
        mycmap = transparent_cmap(plt.cm.gnuplot)
        # mycmap = transparent_cmap(plt.cm.bone)

        # Make a grid to sample on (randomized a little bit).
        rows, cols = self.get_points(max_number=max_number)
        grid_rows = np.linspace(
            0, self.height, spacing
        )  # + 10 * (np.random.rand(512) - 0.5)
        grid_cols = np.linspace(
            0, self.width, spacing
        )  # + 10 * (np.random.rand(512) - 0.5)
        axes = np.array([grid_cols, grid_rows])
        pdf, axes = fastKDE.pdf(cols, rows, axes=axes)
        pdf[pdf < 0] = np.min(pdf[pdf > 0])
        pdf -= pdf.min()

        # Normalize the PDF to compare across maps.
        # pdf -= pdf.mean()
        pdf /= pdf.max()

        # mg, _ = np.meshgrid(grid_rows, grid_cols)
        # for point in tqdm(axes.T):
        #     col = int(point[0])
        #     row = int(point[1])
        #     debug()
        #     if row < self.height and col < self.width:
        #         if self.map_image[int(np.floor(row)), int(np.floor(col)), :].sum() == 0:
        #             r_ = np.argmin(np.abs(grid_rows - row))
        #             c_ = np.argmin(np.abs(grid_cols - col))
        #             pdf[r_, c_] = pdf.max()

        # Make the plot!
        plt.close("all")
        plt.ion()
        fig, ax = plt.subplots(1, 1)
        # fig.set_size_inches(width / 220, height / 220)
        ax.imshow(self.map_image)
        cb = ax.contourf(axes[0], axes[1], pdf, 15, cmap=mycmap, antialiased=True)
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


def transparent_cmap(cmap, N=255):
    "Copy colormap and set alpha values"
    mycmap = cmap
    mycmap._init()
    lp = np.linspace(0, 1, N + 4) - 0.25
    alpha = 10
    mycmap._lut[:, -1] = np.exp(alpha * lp) / (1 + np.exp(alpha * lp))
    # mycmap._lut[:, -1] = np.linspace(0, 0.99, N + 4)
    return mycmap


if __name__ == "__main__":
    # Grab a map.
    # target = "JUL"
    # target = "AUG"
    target = "elberta_centaurea_06"
    maps = db.get_maps()
    if target == "frangula_st_johns_07":
        map_dict = maps[5]
        map_data = frangula_07
    elif target == "frangula_st_johns_08":
        map_dict = maps[6]
        map_data = frangula_08
    elif target == "elberta_centaurea_06":
        map_dict = maps[3]
        map_data = elberta_centaurea_06

    # Construct a heatmap object and plot the density.
    hm = HeatMap(map_dict, map_data)
    hm.plot_density()
