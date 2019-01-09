from vessel import Vessel
import pylab as plt
import numpy as np


plt.ion()
plt.close("all")

v = Vessel("batch.dat")
X, y = v.X, v.y

idx = np.random.randint(500)
plt.imshow(X[idx, :])
