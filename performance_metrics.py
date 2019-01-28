from cnn import *
from config import *
from generate_batch import *
from vessel import Vessel

import numpy as np
from tqdm import tqdm


class ROC:
    """Generate a ROC curve, etc."""

    def __init__(self, scientific_name):
        """Generate a ROC curve for the specified target."""
        # If no valid batch is present, let's create one before training.
        invalid_batch = True
        batch = Vessel("batch.dat")
        if "scientific_name" in batch.keys:
            if batch.scientific_name == scientific_name:
                invalid_batch = False
        if invalid_batch:
            batch = create_batch(scientific_name)
        self.X, self.y = batch.X, batch.y
        self.scientific_name = scientific_name
        self.cnn = CNN(scientific_name, do_load_model=True)
        self.evaluate()

    def evaluate(self):
        """Load results, or calculate them if not available."""
        results = Vessel("predictions.dat")
        if "y_" not in results.keys or results.scientific_name != self.scientific_name:
            self.y_ = self.cnn.model.predict(self.X)
            results.y = self.y
            results.y_ = self.y_
            results.scientific_name = self.scientific_name
            results.save()
        self.y_ = results.y_

    def true_positive(self, y_, thresh):
        """Compute the true positive rate."""
        # Find all samples that are actually positive.
        pos_idx = np.nonzero(self.y == 1)[0]
        y = self.y[pos_idx]
        y_ = (self.y_[pos_idx]).flatten()
        y_[y_ >= thresh] = 1
        y_[y_ < thresh] = 0
        tp = (y_ == 1).sum() / len(y_)
        return tp

    def true_negative(self, y_, thresh):
        """Compute the true negative rate."""
        # Find all samples that are actually positive.
        neg_idx = np.nonzero(self.y == 0)[0]
        y = self.y[neg_idx]
        y_ = (self.y_[neg_idx]).flatten()
        y_[y_ >= thresh] = 1
        y_[y_ < thresh] = 0
        tn = (y_ == 0).sum() / len(y_)
        return tn

    def false_positive(self, y_, thresh):
        """Compute the false positive rate."""
        # Find all samples that are actually positive.
        neg_idx = np.nonzero(self.y == 0)[0]
        y = self.y[neg_idx]
        y_ = (self.y_[neg_idx]).flatten()
        y_[y_ >= thresh] = 1
        y_[y_ < thresh] = 0
        fp = (y_ == 1).sum() / len(y_)
        return fp

    def false_negative(self, y_, thresh):
        """Compute the false negative rate."""
        # Find all samples that are actually positive.
        pos_idx = np.nonzero(self.y == 1)[0]
        y = self.y[pos_idx]
        y_ = (self.y_[pos_idx]).flatten()
        y_[y_ >= thresh] = 1
        y_[y_ < thresh] = 0
        fn = (y_ == 0).sum() / len(y_)
        return fn

    def sensitivity(self):
        """Compute the sensitivity of the classifier."""
        pass

    def auc(self):
        """Compute the area under the ROC curve."""
        fps, tps, threshes = self.calculate_roc()
        # Sort by fps.
        idx = np.argsort(fps)
        fps_ = fps[idx]
        tps_ = tps[idx]
        return self.monte_carlo(fps, tps, nb_itr=20000)

    def monte_carlo(self, fps, tps, nb_itr=1000):
        """Use Monte Carlo to calculate area under ROC."""
        random = np.random.rand(2, nb_itr)
        under_curve = 0
        for r in random.T:
            pos = np.argmin(np.abs(fps - r[0]))
            if tps[pos] < r[1]:
                under_curve += 1
        auc = under_curve / nb_itr
        return auc

    def calculate_roc(self):
        """Calculate probabilities for all the samples."""
        tps = []
        fps = []
        y_ = np.copy(self.y_)
        thresholds = np.linspace(0, 1.01, 1000)
        for thresh in thresholds:
            tps.append(self.true_positive(y_, thresh))
            fps.append(self.false_positive(y_, thresh))
        return np.array(tps), np.array(fps), thresholds

    def calculate_stats(self):
        """Calculate probabilities for all the samples."""
        tps = []
        tns = []
        fps = []
        fns = []
        y_ = np.copy(self.y_)
        thresholds = np.linspace(0, 1.01, 1000)
        for thresh in thresholds:
            tps.append(self.true_positive(y_, thresh))
            tns.append(self.true_negative(y_, thresh))
            fps.append(self.false_positive(y_, thresh))
            fns.append(self.false_negative(y_, thresh))
        tps = np.array(tps)
        tns = np.array(tns)
        fps = np.array(fps)
        sensitivity = tps / (tps + fns)
        specificity = tns / (tns + fps)
        return sensitivity, specificity


class ConfusionMatrix:
    """Create a confusion matrix for a given list of target species."""

    def __init__(self, target_species=TARGET_SPECIES, load_vessel=False):
        """Specific the list of scientific names of interest."""
        # Specify the target species for the confusion matrix.
        self.target_species = target_species

        # Load data for each target species.
        if load_vessel:
            v = Vessel("confusion.dat")
            self.X = v.X
            self.y = v.y
        else:
            self.load_targets()

    def classify_tiles(self):
        """Classify all the tiles."""
        scores = {}
        for scientific_name in self.target_species:
            cnn = CNN(scientific_name, do_load_model=True)
            scores[scientific_name] = cnn.model.predict(np.array(cm.X))
        self.scores = scores
        cm = Vessel('confusion_matrix.dat')
        cm.scores = scores
        cm.save()

    def load_targets(self):
        """Load example targets."""
        y = []
        X = []
        print("> Assembling the data.")
        for scientific_name in tqdm(self.target_species):
            annotations = get_specified_target(scientific_name, nb_annotations=100)
            for annotation in tqdm(annotations):
                X_ = extract_tiles_from_annotation(annotation, 10)
                X.extend(X_)
                y_ = [scientific_name] * len(X_)
                y.extend(y_)
        self.X = X
        self.y = y
        print("> Assembly complete.")
        c = Vessel("confusion_matrix.dat")
        c.X = X
        c.y = y
        c.save()


if __name__ == "__main__":
    from pylab import ion, close, figure, plot, xlabel, ylabel, ylim, xlim
    import pylab as plt
    import seaborn as sns

    # Generate a ROC curve for these guys.
    scientific_name = "Frangula alnus"
    # scientific_name = "Centaurea stoebe"
    # scientific_name = "Phragmites australis subsp australis"
    roc = ROC(scientific_name)
    tps, fps, thresholds = roc.calculate_roc()
    auc = roc.auc()

    ion()
    close("all")
    figure(figsize=(10, 8))
    sns.set_context("poster")
    plot(fps, tps)
    plt.fill_between(fps, tps, np.zeros_like(tps), alpha=0.3)
    plt.grid(True)
    xlim([0, 1.05])
    ylim([0, 1.05])
    xlabel("False Positive Rate")
    ylabel("True Positive Rate")
    plt.axis("equal")
    plt.title(f"{scientific_name} — AUC = {auc*100:.1f}%")
    plt.savefig(f"imgs/AUC_{scientific_name}.png")
