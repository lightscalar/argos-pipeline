from osgeo import gdal, osr
from glob import glob
from ipdb import set_trace as debug
from matplotlib.pyplot import plot, close, ion, imread
from matplotlib.pyplot import figure, xlim, ylim, xlabel, ylabel, imshow
import matplotlib.pyplot as plt
import numpy as np


# Where are the maps located?
map_dir = "maps"
date = "2018.08.03"
location = "St_Johns_Marsh_(66)"
location = "Algonac_State_Park_(66)"

maps = glob(f"{map_dir}/{date}/{location}/*.tif")
path_to_geo_map = maps[0]
path_to_density_map = "algonac_buckthorn.png"

# Load the density map.
img = plt.imread(path_to_density_map)

# Boot up the GTiff driver.
gtiff_driver = gdal.GetDriverByName("GTiff")

# Make a new geotiff file.
out_ds = gtiff_driver.Create("algonac_state_park_buckthorn.tif", img.shape[1], img.shape[0], 3, 1)

# Crack open the original georeferenced image.
ds = gdal.Open(path_to_geo_map)

# Set the geotransform and projection properly.
out_ds.SetProjection(ds.GetProjection())
out_ds.SetGeoTransform(ds.GetGeoTransform())

# Band indices start at 1, yo.
for band_number in np.arange(1, 4):
    band_data = img[:, :, 3 - band_number]
    band_data =(255 * band_data).astype(int)
    out_band = out_ds.GetRasterBand(4 - int(band_number))
    out_band.WriteArray(band_data)

out_ds.FlushCache()
del out_ds
