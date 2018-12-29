from config import *
from database import *
from utils import *

from bs4 import BeautifulSoup
from glob import glob
from imageio import imwrite
from ipdb import set_trace as debug
import numpy as np
from skimage import io
from tqdm import tqdm


def relabel_keys(dict_obj, prepend_label):
    """Prepend a label to all keys in a dictionary."""
    obj = {}
    for key, val in dict_obj.items():
        obj[f"{prepend_label}_{key}"] = val
    return obj


def ingest_kml_file(map_object):
    """Read KML files associated with maps, if available."""
    path_to_small_kml = map_object["path_to_small_kml"]
    path_to_map_kml = map_object["path_to_map_kml"]
    path_to_small_kml = prepend_argos_root(path_to_small_kml)
    path_to_map_kml = prepend_argos_root(path_to_map_kml)
    if len(glob(path_to_map_kml)) > 0:
        kml = parse_keyhole(path_to_map_kml)
        # kml = relabel_keys(kml, 'map')
    else:
        kml = None
    if len(glob(path_to_small_kml)) > 0:
        small_kml = parse_keyhole(path_to_small_kml)
        # small_kml = relabel_keys(small_kml, 'small')
    else:
        small_kml = None
    return kml, small_kml


def parse_keyhole(path_to_kml_file):
    """Parse (for our purposes) a KML file."""
    document = open(path_to_kml_file)
    xml = document.read()
    data = BeautifulSoup(xml, "xml")
    out = {}
    # Extract lat/lon boundaries of the specified image.
    out["north"] = float(data.north.contents[0])
    out["south"] = float(data.south.contents[0])
    out["east"] = float(data.east.contents[0])
    out["west"] = float(data.west.contents[0])
    return out


def read_associated_kml_file(path_to_tile):
    """Look for and parse associated KML file. Throw error if none exists."""
    path_list = path_to_tile.split("/")
    root_path = "/".join(path_list[:-1])
    tile_name = path_list[-1][:-4]
    path_to_kml_list = glob(f"{root_path}/{tile_name}.kml")
    if len(path_to_kml_list) == 0:
        raise ValueError("No associated KML file exists.")
    else:
        path_to_kml = path_to_kml_list[0]
    return parse_keyhole(path_to_kml)


def split_tile(path_to_tile, tile_size=2048, tile_number=1):
    """Split a tile into squares of dimension <tile_size>."""
    tn = tile_number
    path_list = pl = path_to_tile.split("/")
    root_path = rp = "/".join(path_list[:-1])  # absolute path
    relative_path = (
        f"{pl[-7]}/{pl[-6]}/{pl[-5]}/{pl[-4]}/{pl[-3]}/tiles"
    )  # relative path
    tile = io.imread(path_to_tile)[:, :, :]  # only grab three color channels
    height, width, channels = tile.shape
    kml = read_associated_kml_file(path_to_tile)
    latitudes = np.linspace(kml["north"], kml["south"], height)
    longitudes = np.linspace(kml["west"], kml["east"], width)
    nb_cols = int(width / tile_size)
    nb_rows = int(height / tile_size)
    ts = tile_size
    itr = 0
    for c in np.arange(nb_cols):
        west = longitudes[c * ts]
        east = longitudes[ts * (c + 1) - 1]
        lon_ = (west + east) / 2
        for r in np.arange(nb_rows):
            itr += 1
            # Extract sub-tile from large tile.
            tile_ = tile[r * ts : (r + 1) * ts, c * ts : (c + 1) * ts, :]
            north = latitudes[r * ts]
            south = latitudes[ts * (r + 1) - 1]
            lat_ = (north + south) / 2
            absolute_path_to_sub_tile = f"{root_path}/TILE_{tn:04d}_{itr:04d}.png"
            relative_path_to_sub_tile = f"{relative_path}/TILE_{tn:04d}_{itr:04d}.png"
            tile_id = (
                f"{pl[-7]}-{pl[-6]}-{pl[-5]}-{pl[-4]}-{pl[-3]}-TILE_{tn:04d}_{itr:04d}"
            )
            tile_obj = {
                "tile_id": tile_id,
                "north": north,
                "south": south,
                "west": west,
                "east": east,
                "path_to_tile": relative_path_to_sub_tile,
            }
            imwrite(absolute_path_to_sub_tile, tile_)
            db.insert_tile(tile_obj)


def process_tiles(path_to_tiles, tile_size=2048):
    """Process an entire directory of tiles. Insert them into database."""
    tiles = glob(f"{path_to_tiles}/*.tif")
    tiles = sorted(tiles)
    for tile_number, path_to_tile in enumerate(tqdm(tiles)):
        split_tile(path_to_tile, tile_number=tile_number)

    return tiles


if __name__ == "__main__":
    path_to_tiles = f"{ARGOS_ROOT}/2018/08/03/st_johns_marsh/66/tiles"
    # tiles = glob("imgs/tiles/*.tif")
    # split_tile(tiles[0])
    # tiles = process_tiles(path_to_tiles)
