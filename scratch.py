from database import *
from utils import *
from vessel import *

import numpy as np
import pylab as plt


if __name__ == "__main__":

    # Load annotations.
    path_to_annotations = "data/2019.01.07_legacy_annotations.dat"
    annotations = Vessel(path_to_annotations).annotations
    nb_annotations = len(annotations)

    # Verify that annotations is working okay.
    no_image = True
    while no_image:
        try:
            annot_idx = np.random.randint(nb_annotations)
            annot = annotations[annot_idx]
            image_dict = parse_image_id(annot["image_id"])
            image = plt.imread(prepend_argos_root(image_dict["path_to_image"]))
            no_image = False
        except:
            no_image = True

    # Parse the image ID.
    rows, cols, chans = image.shape
    row = annot["alpha"] * rows
    col = annot["beta"] * cols
    plt.ion()
    plt.close("all")
    plt.figure()
    plt.imshow(image)
    plt.plot(col, row, "rs")
    print(annot)

    # Extract tiles from this guy.
    examples = extract_tiles(image, row, col)
    plt.figure()
    for k in range(10):
        plt.subplot(f"52{k}")
        fig = plt.imshow(examples[k])
        fig.axes.get_xaxis().set_visible(False)
        fig.axes.get_yaxis().set_visible(False)

    negative_pipeline = [
        {"$sample": {"size": 10000}},
        {"$match": {"scientific_name": {"$ne":  "Frangula alnus"}}},
    ]
    positive_pipeline = [
        {"$sample": {"size": 10000}},
        {"$match": {"scientific_name": "Frangula alnus"}},
    ]


    negative_samples = list(db.annotations.aggregate(negative_pipeline))
    positive_samples = list(db.annotations.aggregate(positive_pipeline))

    for sample in negative_samples:
        if sample['scientific_name'] == 'Frangula alnus':
            debug()
    for sample in positive_samples:
        if sample['scientific_name'] != 'Frangula alnus':
            debug()
