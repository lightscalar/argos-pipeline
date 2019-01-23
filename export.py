"""Tools for importing and exporting data from MongoDB."""
from database import *
from vessel import *


def export_data(path_to_export_file):
    """Write data to a portable file."""
    v = Vessel(path_to_export_file)
    print(f"> Saving data to {path_to_export_file}")
    v.targets = db.get_targets()
    v.ground_truth = db.get_ground_truths()
    v.tiles = db.get_tiles()
    v.maps = db.get_maps()
    v.imagery = db.get_images()
    v.annotations = db.get_annotations()
    v.save()


def import_annotations(path_to_import_file):
    """Import annotations to the MongoDB."""
    # Import annotations.
    v = Vessel(path_to_import_file)
    try:  # to import all; some may fail, but the rest will be inserted.
        db.annotations.insert_many(v.annotations, ordered=False)
    except:
        print("> Existing annotations were not inserted.")


def import_maps(path_to_import_file):
    """Import maps to the MongoDB."""
    # Import annotations.
    v = Vessel(path_to_import_file)
    try:  # to import all; some may fail, but the rest will be inserted.
        db.maps.insert_many(v.maps, ordered=False)
    except:
        print("> Existing maps were not inserted.")


def import_data(path_to_import_file, do_not_import=[], replace=[]):
    """Import data into the database."""
    v = Vessel(path_to_import_file)

    # Import data into database (tries/catch overwriting).
    if "maps" not in do_not_import:
        try:
            if "maps" in replace:
                db.maps.delete_many({})
            db.maps.insert_many(v.maps, ordered=False)
        except:
            print("> Existing maps were not inserted.")

    # Import targets.
    if "targets" not in do_not_import:
        try:
            if "targets" in replace:
                db.targets.delete_many({})
            db.targets.insert_many(v.targets, ordered=False)
        except:
            print("> Existing targets were not inserted.")

    # Import imagery.
    if "imagery" not in do_not_import:
        try:
            if "imagery" in replace:
                db.imagery.delete_many({})
            db.imagery.insert_many(v.imagery, ordered=False)
        except:
            print("> Existing imagery was not inserted.")

    # Import ground truth.
    if "ground_truth" not in do_not_import:
        try:
            if "ground_truth" in replace:
                db.ground_truth.delete_many({})
            db.ground_truths.insert_many(v.ground_truth, ordered=False)
        except:
            print("> Existing ground truths were not inserted.")

    # Import annotations.
    if "annotations" not in do_not_import:
        try:
            if "annotations" in replace:
                db.annotations.delete_many({})
            db.annotations.insert_many(v.annotations, ordered=False)
        except:
            print("> Existing annotations were not inserted.")

    # Import tiles.
    if "tiles" not in do_not_import:
        try:
            if "tiles" in replace:
                db.tiles.delete_many({})
            db.tiles.insert_many(v.tiles, ordered=False)
        except:
            print("> Existing tiles were not inserted.")
