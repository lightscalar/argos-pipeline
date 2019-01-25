"""Quickly visualize the current batch of training data."""
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
    v = Vessel("batch.dat")
    X, y = v.X, v.y

    targets = np.nonzero(y == 1)[0]
    confusors = np.nonzero(y == 0)[0]

    # Load the example data.
    ion()
    close("all")
    max_confusors = 600

    figure()
    subplot("221")
    idx = targets[np.random.randint(1000)]
    imshow(X[idx, :])
    subplot("222")
    idx = confusors[np.random.randint(max_confusors)]
    imshow(X[idx, :])
    subplot("223")
    idx = confusors[np.random.randint(max_confusors)]
    imshow(X[idx, :])
    subplot("224")
    idx = confusors[np.random.randint(max_confusors)]
    imshow(X[idx, :])
