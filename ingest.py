"""Utilities for ingesting ground truth and annotation target information."""
from config import *
from database import *

import numpy as np
import pandas as pd
import seaborn as sns


# Define some nice, random colors.
np.random.seed(0)
colors = list(sns.xkcd_rgb.keys())
np.random.shuffle(colors)


if __name__ == "__main__":

    # Ingest all available annotation targets.
    targets_excel = pd.read_excel(f"{TARGET_FILE}")
    scientific_names = np.unique(list(targets_excel["Scientific Name"]))
    targets = []

    for scientific_name in scientific_names:
        if scientific_name != "nan":
            target = {}
            target["scientific_name"] = scientific_name
            target["codes"] = set([])
            for idx, name in enumerate(targets_excel["Scientific Name"]):
                if name == scientific_name:
                    target["common_name"] = targets_excel["Common Name"][idx]
                    target["physiognomy"] = targets_excel["PHYSIOGNOMY"][idx]
                    target["category"] = targets_excel["CATEGORY"][idx]
                    target["color_code"] = sns.xkcd_rgb[colors[idx]]
                    codes = targets_excel["Code"][idx].split(" ")
                    for code in codes:
                        target["codes"].add(code)
            targets.append(target)
        else:
            continue

    # Remove sets.
    for target in targets:
        target["codes"] = list(target["codes"])

    water = {
        "scientific_name": "H2O",
        "codes": ["CR"],
        "common_name": "water",
        "physiognomy": "N/A",
        "category": "Physical Feature",
        "color_code": "#0e87cc",
    }
    street = {
        "scientific_name": "Roadus Roadius",
        "codes": ["ROAD"],
        "common_name": "Road",
        "physiognomy": "N/A",
        "category": "Man-made Feature",
        "color_code": "#070d0d",
    }
    sand = {
        "scientific_name": "Silicon Dioxide",
        "codes": ["DIRT"],
        "common_name": "Sand",
        "physiognomy": "N/A",
        "category": "Physical Feature",
        "color_code": "#8a6e45",
    }
    rock = {
        "scientific_name": "Rocky Rockinius",
        "codes": ["ROCK"],
        "common_name": "Rock",
        "physiognomy": "N/A",
        "category": "Physical Feature",
        "color_code": "#ada587",
    }

    # Add additional
    targets.append(water)
    targets.append(street)
    targets.append(sand)
    targets.append(rock)

    # Add the plants to the database.
    target_collection.delete_many({})  # first get rid of all of them.
    target_collection.insert_many(targets)

    # Next we ingest all available ground truth data.
