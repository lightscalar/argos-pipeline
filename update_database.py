"""Utilities to help changeover to tile-based system."""
from database import *
from read_kml import parse_keyhole, ingest_kml_file
from ipdb import set_trace as debug


if __name__ == "__main__":
    # Ensure maps all have a path_to_tiles entry.
    maps = db.get_maps(return_id=True)
    for mp in maps:
        mp["path_to_map_kml"] = mp["path_to_images"].replace("images", "maps/map.kml")
        mp["path_to_small_kml"] = mp["path_to_images"].replace(
            "images", "maps/map_small.kml"
        )
        mp["path_to_tiles"] = mp["path_to_images"].replace("images", "tiles")
        kml, small_kml = ingest_kml_file(mp)
        if kml:
            mp['map_boundaries'] = kml
        if small_kml:
            mp['small_map_boundaries'] = small_kml
        db.update_map(mp)
