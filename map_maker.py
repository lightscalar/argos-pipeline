from config import *
from database import *
from cnn import *
from mcmc import *
import scipy.spatial as spatial


if __name__ == "__main__":

    # Grab a map.
    maps = db.get_maps()
    my_map = maps[4]
    scientific_name = "Frangula alnus"
    cnn = CNN(scientific_name, do_load_model=True)

    # Find images.
    path_to_images = f"{prepend_argos_root(my_map['path_to_images'])}/*.JPG"
    images = glob(path_to_images)

    # Load image.
    from pylab import imshow, ion, close

    ion()
    close("all")

    images = sorted(images)
    image_nb = 903
    image = plt.imread(images[image_nb])
    cnn.set_image(images[image_nb])
    pdf = cnn.predict

    # Scan image.
    alpha = np.linspace(0, 1, 40)
    beta = np.linspace(0, 1, 40)
    X = []
    P = []
    for a in tqdm(alpha):
        for b in beta:
            p = cnn.predict([a, b])
            P.append(p)
            X.append([a, b])
    X_ = [x for p,x in zip(P,X) if p>0.9]
    P_ = [p for p,x in zip(P,X) if p>0.9]
    tree = spatial.cKDTree(X_)

    # X = []
    # P = []
    # for k in range(10):
    #     X_, P_ = mcmc(pdf, nb_iter=50)
    #     X.extend(X_)
    #     P.extend(P_)

    plt.close("all")
    imshow(image)
    for p, x in zip(P_, X_):
        if p > 0.9 and len(tree.query_ball_point(x, 0.05)) > 2:
            plt.plot(x[1] * 4000, x[0] * 3000, "ro", alpha=p)
