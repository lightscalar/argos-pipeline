from database import *

from glob import glob
import re
from vessel import *


if __name__ == "__main__":

    v = Vessel("data/annotated_images.dat")

    rgx = r"2018.06.27.*Elberta"
    candidates = []
    sites = []
    for itr, annot in enumerate(v.annotated_images):
        match = re.search(rgx, annot["local_location"])
        if match is not None:
            path_to_image = annot["local_location"]
            path_list = path_to_image.split("/")
            date = path_list[-3]
            site = path_list[-2]
            site_name = re.search(r"([\w\.\s]+)", site)[1].strip()
            site_name = site_name.replace(".", "").replace(" ", "_").lower()
            candidates.append(itr)
            sites.append(site_name)
