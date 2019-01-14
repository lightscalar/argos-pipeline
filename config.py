"""Useful configuration parameters and constants."""
import getpass
from glob import glob


# Find the current user.
user = getpass.getuser()
EPSG = 4326

# Define confusors.
CONFUSORS = {}
CONFUSORS["Frangula alnus"] = [
    "Achillea millifolium",
    "Andropogan gerardii",
    "Animal generalis",
    "Antus_Moundus",
    "Calamagrostis canadensis",
    "Carex",
    "Cornus",
    "Cuscuta_gronovii",
    "Joshua floristis",
    "Leafy litteris",
    "Liatris spicata",
    "Matthew pilotis",
    "Phalaris arundinacea",
    "Phragmites australis subsp australis",
    "Populus deltoides",
    "Populus tremuloides",
    "Quercus",
    "Railroadus_gradus",
    "Rhamnus cathartica",
    "Rhus aromatica",
    "Solidago",
    "Spartina pectinata",
    "Verbascum thapsus",
    "Vernonia_missurica",
    "Veronicastrum virginicum",
]

# Determine location of image data based on current user.
if user == "mjl":
    ARGOS_ROOT = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/ARGOS"
    TARGET_FILE = "truth/target_key.xlsx"
    TRUTH_FILES = glob("truth/*.shp")
    MODEL_LOCATION = "data/models"
elif user == "jgc":  # we're on Josh's laptop
    ARGOS_ROOT = "/Users/jgc/ARGOS"
    TARGET_FILE = "truth/target_key.xlsx"
    TRUTH_FILES = glob("truth/*.shp")
    MODEL_LOCATION = "data/models"
elif user == "mlewis":  # we're deployed on Zee
    ARGOS_ROOT = "/mnt/scratch/ARGOS"
    MODEL_LOCATION = "data/models"
