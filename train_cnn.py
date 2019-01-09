"""Generate a batch of training data (in a separate process, usually)."""
from database import *

import argparse


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
    default=25,
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

