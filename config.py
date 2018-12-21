"""Useful configuration parameters and constants."""
import getpass
from glob import glob


# Find the current user.
user = getpass.getuser()
EPSG = 4326

# Determine location of image data based on current user.
if user == "mjl":
    ARGOS_ROOT = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/ARGOS"
    TARGET_FILE = "truth/target_key.xlsx"
    TRUTH_FILES = glob("truth/*.shp")
    # IMAGE_LOCATION = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/MNFI/FLIGHTS"
    # IMAGE_SERVER_LOCATION = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/MNFI"
    # THUMBNAIL_LOCATION = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/MNFI/THUMBNAILS"
    # API_LOCATION = "/Users/mjl/dev/mnfi/argos/api"
    # STATIC_LOCATION = "/Users/mjl/dev/mnfi/argos/dist"
    # MODEL_LOCATION = "/Users/mjl/dev/mnfi/argos_pipeline/data/models"
elif user == "jgc": # we're on Josh's laptop
    ARGOS_ROOT = "/Users/jgc/ARGOS"
    TARGET_FILE = "truth/target_key.xlsx"
    TRUTH_FILES = glob("truth/*.shp")
elif user="mlewis": # we're deployed on Zee
    ARGOS_ROOT="/mnt/scratch/ARGOS"
