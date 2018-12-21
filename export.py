"""Tools for importing and exporting data from MongoDB."""
from database import *
from vessel import *


def export_data(path_to_export_file):
    """Write data to a portable file."""
    v = Vessel(path_to_export_file)
    print(f"> Saving data to {path_to_export_file}")
    v.targets = list(target_collection.find({}))
    v.ground_truth = list(ground_truth_collection.find({}))
    v.imagery = list(imagery_collection.find({}))
    v.annotations = list(annotations_collection.find({}))
    v.maps = list(map_collection.find({}))
    v.save()


def import_data(path_to_import_file):
    """Import data into the database."""
    v = Vessel(path_to_import_file)

    # Import data into database (tries catch overwriting).
    # Import maps.
    try:
        map_collection.insert_many(v.maps, ordered=False)
    except:
        print("> Existing maps were not inserted.")

    # Import targets.
    try:
        target_collection.insert_many(v.targets, ordered=False)
    except:
        print("> Existing targets were not inserted.")

    # Import imagery.
    try:
        imagery_collection.insert_many(v.imagery, ordered=False)
    except:
        print("> Existing imagery was not inserted.")

    # Import ground truth.
    try:
        ground_truth_collection.insert_many(v.ground_truth, ordered=False)
    except:
        print("> Existing maps were not inserted.")

    # Import annotations.
    try:
        annotations_collection.insert_many(v.annotations, ordered=False)
    except:
        print("> Existing annotations were not inserted.")
