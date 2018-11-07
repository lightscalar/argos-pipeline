#!python

import numpy as np
from fastkde import fastKDE
import pylab as PP

#Generate two random variables dataset (representing 100000 pairs of datapoints)
N = int(2e5)
var1 = 50*np.random.normal(size=N) + 0.1
var2 = 0.01*np.random.normal(size=N) - 300

# Do the self-consistent density estimate
myPDF,axes = fastKDE.pdf(var1,var2)

#Extract the axes from the axis list
v1,v2 = axes

#Plot contours of the PDF should be a set of concentric ellipsoids centered on
#(0.1, -300) Comparitively, the y axis range should be tiny and the x axis range
#should be large
PP.ion()
PP.contour(v1,v2,myPDF)
