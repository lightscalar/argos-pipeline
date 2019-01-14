from vessel import Vessel
import numpy as np
from pylab import (
    ion,
    close,
    plot,
    imshow,
    imread,
    xlabel,
    ylabel,
    xlim,
    ylim,
    subplot,
    figure,
)


if __name__ == "__main__":

    # Load the example data.
    v = Vessel("example_batch.dat")
    X, y = v.X, v.y

    # Load the example data.
    ion()
    close("all")

    figure()
    subplot("221")
    imshow(X[np.random.randint(1000), :])
    subplot("222")
    imshow(X[np.random.randint(1000), :])
    subplot("223")
    idx = np.random.randint(800) + 1010
    imshow(X[idx, :])
    subplot("224")
    idx = np.random.randint(800) + 1010
    imshow(X[idx, :])
