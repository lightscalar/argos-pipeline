"""Utilities to help changeover to tile-based system."""
from database import *
from read_kml import parse_keyhole, ingest_kml_file

from ipdb import set_trace as debug
from tqdm import tqdm


if __name__ == "__main__":
    # Ensure maps all have a path_to_tiles entry.
    if False:
        maps = db.get_maps(return_id=True)
        for mp in maps:
            mp["path_to_map_kml"] = mp["path_to_images"].replace(
                "images", "maps/map.kml"
            )
            mp["path_to_small_kml"] = mp["path_to_images"].replace(
                "images", "maps/map_small.kml"
            )
            mp["path_to_tiles"] = mp["path_to_images"].replace("images", "tiles")
            kml, small_kml = ingest_kml_file(mp)
            if kml:
                mp["map_boundaries"] = kml
            if small_kml:
                mp["small_map_boundaries"] = small_kml
            db.update_map(mp)

    # Make sure annotations have alpha/beta values.
    if True:
        annotations = db.get_annotations(return_id=True)
        for an in tqdm(annotations):
            if "alpha" not in an.keys():
                an["alpha"] = an["row"]
                an["beta"] = an["col"]
                db.update_annotation(an)
