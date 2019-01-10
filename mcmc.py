import numpy as np
from scipy.stats import multivariate_normal
import pylab as plt
from tqdm import tqdm


def in_box(pos):
    """Determine if position is within bounds."""
    x, y = pos
    return (x >= 0) * (x < 1) * (y >= 0) * (y <= 1)


def transition(position, mean_radius=0.15):
    """Transition to a new point in the plane."""
    angle = np.random.uniform(0, 2 * np.pi)
    radius = mean_radius * np.random.rand()
    step = radius * np.array([np.cos(angle), np.sin(angle)])
    next_position = position + step
    if not in_box(next_position):
        next_position = position
    return next_position


def pdf(position):
    rv1 = multivariate_normal([0.6, .650], [[.0950, .023], [.0300, .0600]])
    rv2 = multivariate_normal([.400, .250], [[.0150, .023], [.023, .060]])
    return rv1.pdf(position) + rv2.pdf(position)


def mcmc(pdf, nb_iter=1500):
    """Metropolis-Hasting algorithm for PDF sampling."""
    X = []
    P = []
    x = np.array([1 * np.random.rand(), 1 * np.random.rand()])
    X.append(x)
    P.append(pdf(x))
    for itr in tqdm(range(nb_iter)):
        px = pdf(x)
        x_ = transition(x)
        px_ = pdf(x_)
        r = px_ / px
        if r > 1 or (np.random.rand() < r):
            x = x_
            if itr > 0.30 * nb_iter:
                X.append(x)
                P.append(px_)
    return X, P


if __name__ == "__main__":

    # Set up the parameters.
    max_x = 1
    max_y = 1
    X = []
    for k in range(5):
        X.extend(mcmc(pdf))
    X = np.array(X)

    plt.ion()
    plt.close("all")
    plt.plot(X[:, 0], X[:, 1], alpha=0.2)
    plt.plot(X[:, 0], X[:, 1], ".")
    plt.xlim([0, 1])
    plt.ylim([0, 1])
