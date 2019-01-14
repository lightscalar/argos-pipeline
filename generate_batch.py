"""Generate a batch of training data (in a separate process, usually)."""
from database import *

import argparse


def create_batch(scientific_name, tiles_per_class, samples_per_tile):
    """Create a batch and save to the disk."""
    # Generate some samples.
    print("> Please wait: creating fresh batch.")
    X, y = smart_batch(scientific_name)

    # Save the batch to the disk.
    v = Vessel("batch.dat")
    v.scientific_name = scientific_name
    v.X = X
    v.y = y
    v.save()
    return v


if __name__ == "__main__":

    # Check for arguments.
    parser = argparse.ArgumentParser(description="Create a new batch of training data.")
    parser.add_argument(
        "-n",
        "--name",
        nargs="?",
        default="Frangula alnus",
        type=str,
        help="Scientific name of batch target.",
    )
    parser.add_argument(
        "-s",
        "--samples_per_tile",
        nargs="?",
        default=10,
        type=int,
        help="Number of augmented samples to generate from each annotated tile.",
    )
    parser.add_argument(
        "-t",
        "--tiles_per_class",
        nargs="?",
        default=1000,
        type=int,
        help="Number of tiles per class in a given training batch.",
    )

    # Grab options from the parser.
    args = parser.parse_args()
    scientific_name = args.name
    samples_per_tile = args.samples_per_tile
    tiles_per_class = args.tiles_per_class
    print(tiles_per_class)
    create_batch(scientific_name, tiles_per_class, samples_per_tile)
