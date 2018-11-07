from glob import glob
from ipdb import set_trace as debug
import shutil


def convert_site_location(original_name):
    """Convert old-style site location to the new hotness."""
    pass


DEPOT = "/Users/mjl/Dropbox (Personal)/MAC/DEPOT/MNFI/FLIGHTS"
dates = glob(f"{DEPOT}/*")
for date in dates:
    sites = glob(f"{date}/*")
    for site in sites:
        site_array = site.split("/")
        site_name = site_array[-1]
        site_name = (
            site_name.lower()
            .replace(" ", "_")
            .replace(".", "")
            .replace("(", "")
            .replace(")", "")
            .replace("'", "")
        )
        site_array[-1] = site_name
        new_site_location = "/".join(site_array)
        debug()
