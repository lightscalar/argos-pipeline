"""Train a CNN to identify invasive species."""
from config import *
from utils import *

from glob import glob
from keras.callbacks import ModelCheckpoint
from keras.models import load_model, Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.optimizers import Adam
from keras.layers.normalization import BatchNormalization
from keras.utils import np_utils
from keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D, GlobalAveragePooling2D
from tqdm import tqdm


class CNN:
    """Basic CNN for image invasive species detection."""

    def __init__(
        self,
        model_name,
        tile_size=128,
        tiles_per_class=4000,
        nb_epochs_per_iter=10,
        nb_iter=100,
        load_model=False,
    ):
        """Set up the basic convolutional neural network model."""
        self.model_name = model_name
        self.model_location = f"{MODEL_LOCATION}/{model_name}.h5"

        self.tiles_per_class = tiles_per_class
        self.nb_epochs_per_iter = nb_epochs_per_iter
        self.nb_iter = nb_iter
        self.tile_size = tile_size
        if load_model and len(glob(self.model_location)) > 0:
            self.model = load_model(self.model_location)
        else:
            self.build_model()

    def build_model(self):
        """Build the convolutional neural network."""
        tile_size = self.tile_size

        # Build the CNN.
        input_shape = (tile_size, tile_size, 3)

        model = Sequential()
        model.add(Conv2D(32, (3, 3), input_shape=(tile_size, tile_size, 3)))
        model.add(BatchNormalization(axis=-1))
        model.add(Activation("relu"))
        model.add(Conv2D(32, (5, 5)))
        model.add(BatchNormalization(axis=-1))
        model.add(Activation("relu"))
        model.add(MaxPooling2D(pool_size=(2, 2)))

        # Add another hidden layer.
        model.add(Conv2D(64, (7, 7)))
        model.add(BatchNormalization(axis=-1))
        model.add(Activation("relu"))
        model.add(Conv2D(64, (9, 9)))
        model.add(BatchNormalization(axis=-1))
        model.add(Activation("relu"))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Flatten())

        # Full connected layer.
        model.add(Dense(512))
        model.add(BatchNormalization())
        model.add(Activation("relu"))
        model.add(Dense(512))
        model.add(BatchNormalization())
        model.add(Activation("relu"))
        model.add(Dropout(0.2))
        model.add(Dense(1))
        model.add(Activation("sigmoid"))
        model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["acc"])
        self.model = model

    def train_network(self, target_species_code=28):
        """Train the neural network."""
        for itr in tqdm(range(self.nb_iter)):
            # Grab a subset of the total data.
            X, y = extract_balanced_tiles(
                "data/annotated_images.dat", target_species_code
            )
            self.model.fit(X, y, epochs=self.nb_epochs_per_iter, validation_split=0.1)
            self.model.save(self.model_location)


if __name__ == "__main__":

    # Instantiate the CNN.
    cnn = CNN(model_name="phragmites_v1")
    cnn.train_network(target_species_code=28)  # 28 is code for Phragmites australis...
