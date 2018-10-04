"""Find the latitude, longitude position of any pixel in a georeferenced tif file."""

from osgeo import gdal, osr
import numpy as np


def pixel_to_coord(ds, col, row):
    """Convert column and row indices to geodetic coordinates."""

    x_upper_left, xres, xskew, y_upper_left, yskew, yres = ds.GetGeoTransform()

    lon = (xres * col) + (xskew * row) + x_upper_left
    lat = (yskew * col) + (yres * row) + y_upper_left

    source = osr.SpatialReference()
    source.ImportFromWkt(ds.GetProjection())

    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)

    transform = osr.CoordinateTransformation(source, target)
    result = transform.TransformPoint(lon, lat)

    return result[0], result[1]


def coord_to_pixel(ds, lon, lat):
    """Converts latitude, longitude to column, row in the given dataset."""

    # Invert the transformation between coordinate systems.
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)

    target = osr.SpatialReference()
    target.ImportFromWkt(ds.GetProjection())

    transform = osr.CoordinateTransformation(source, target)
    geolon, geolat, _ = transform.TransformPoint(lon, lat)

    x_upper_left, xres, xskew, y_upper_left, yskew, yres = ds.GetGeoTransform()

    # Solve for column and row.
    b = np.array([geolon - x_upper_left, geolat - y_upper_left])
    A = np.array([[xres, xskew], [yskew, yres]])

    x = np.linalg.lstsq(A, b, rcond=None)

    # Returns: col, row.
    return int(x[0][0]), int(x[0][1])


if __name__ == "__main__":

    # Example.
    ds = gdal.Open("MinerStreetSmall.tif")

    lon, lat = pixel_to_coord(ds, ds.RasterXSize, ds.RasterYSize)
    print(f"Raster size (x, y): {ds.RasterXSize}, {ds.RasterYSize}")
    print(f"With pixel offset: {lon}, {lat}")

    print(f"Column, row: {coord_to_pixel(ds, lon, lat)}")
    print("Should be the same as the raster size.")
