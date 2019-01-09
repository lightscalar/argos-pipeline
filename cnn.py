"""Train a CNN to identify invasive species."""
from config import *
from generate_batch import *
from utils import *

from glob import glob
from keras.callbacks import ModelCheckpoint
from keras.models import load_model, Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.optimizers import Adam
from keras.layers.normalization import BatchNormalization
from keras.utils import np_utils
from keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D, GlobalAveragePooling2D
from subprocess import Popen
from tqdm import tqdm


class CNN:
    """Basic CNN for image invasive species detection."""

    def __init__(
        self,
        scientific_name,
        tile_size=128,
        tiles_per_class=1000,
        samples_per_tile=10,
        nb_epochs_per_iter=25,
        nb_iter=1000,
        do_load_model=False,
    ):
        """Set up the basic convolutional neural network model."""
        self.scientific_name = scientific_name
        self.model_name = model_name = scientific_name.replace(" ", "_").lower()
        self.model_location = f"{MODEL_LOCATION}/{model_name}.h5"

        self.tiles_per_class = tiles_per_class
        self.samples_per_tile = samples_per_tile  # i.e., number rotations per tile
        self.nb_epochs_per_iter = nb_epochs_per_iter
        self.nb_iter = nb_iter
        self.tile_size = tile_size
        if do_load_model and len(glob(self.model_location)) > 0:
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

    def train_network(self):
        """Train the neural network."""

        # If no valid batch is present, let's create one before training.
        invalid_batch = True
        batch = Vessel("batch.dat")
        if "scientific_name" in batch.keys:
            if batch.scientific_name == scientific_name:
                invalid_batch = False
        if invalid_batch:
            batch = create_batch(
                scientific_name,
                tiles_per_class=self.tiles_per_class,
                samples_per_tile=self.samples_per_tile,
            )

        # Train the network.
        for itr in tqdm(range(self.nb_iter)):
            # Launch separate process to generate next batch (work in parallel with neural fit).
            Popen(
                [
                    "python",
                    "generate_batch.py",
                    "-n",
                    self.scientific_name,
                    "-s",
                    str(self.samples_per_tile),
                    "-t",
                    str(self.tiles_per_class),
                ]
            )

            # Load the current batch.
            batch = Vessel("batch.dat")
            X, y = batch.X, batch.y

            # Fit the network to the current batch of data
            self.model.fit(X, y, epochs=self.nb_epochs_per_iter, validation_split=0.1)
            self.model.save(self.model_location)

    def set_image(self, path_to_image):
        """Load an image into memory."""
        self.image = plt.imread(path_to_image)
        self.image_height, self.image_width, _ = self.image.shape

    def predict(self, alpha, beta, tile_size=128):
        """Predict class of tile located at position (alpha, beta)."""
        row = self.image_width * alpha
        col = self.image_height * beta
        tile = extract_tiles(
            self.image, row, col, size=128, num_rotations=1, jitter_amplitude=0
        )
        prob = self.model.predict([tile])
        return prob, tile


if __name__ == "__main__":
    training = True

    # Instantiate the CNN.
    scientific_name = "Frangula alnus"
    if training:
        cnn = CNN(scientific_name, do_load_model=False)
        cnn.train_network()
    else:
        from pylab import imshow, ion, close

        ion()
        close("all")
        cnn = CNN(scientific_name, do_load_model=True)
        images = db.get_images()
        img = images[2137]
        path_to_image = prepend_argos_root(img["path_to_image"])
        cnn.set_image(path_to_image)
