"""A bank of convolutional neural networks, one for each species of interest."""
from config import *

from keras.models import load_model


class NeuralBank:
    """Hold on to neural networks for species of interest (SoI)."""

    def __init__(self, soi_codes=[14, 28]):
        """Specify species models to build."""
        self.soi_codes = soi_codes
        self.cnn_locations = {
            code: f"{MODEL_LOCATION}/cnn_{code:02d}.h5" for code in soi_codes
        }
        self.load_models()

    def load_models(self):
        """Loading the neural network models."""
        self.models = {}
        for code in self.soi_codes:
            print(f"> Loading CNN for species code {code:02d}.")
            self.models[code] = load_model(self.cnn_locations[code])
            print("> Complete.")


# Load the NeuralBank (for import into other scripts).
bank = NeuralBank()
