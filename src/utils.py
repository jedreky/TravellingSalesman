import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
import random
import string
import waitress

SOLVER_PORT_ENV_VAR = "SOLVER_PORT"
assert (
    SOLVER_PORT_ENV_VAR in os.environ
), f"Missing environmental variable: {SOLVER_PORT_ENV_VAR}"
SOLVER_PORT = os.environ.get(SOLVER_PORT_ENV_VAR)

WEBAPP_PORT_ENV_VAR = "WEBAPP_PORT"
assert (
    WEBAPP_PORT_ENV_VAR in os.environ
), f"Missing environmental variable: {WEBAPP_PORT_ENV_VAR}"
WEBAPP_PORT = os.environ.get(WEBAPP_PORT_ENV_VAR)

DPI = 100
HOST = "0.0.0.0"

IMG_FOLDER = Path("src/static/imgs")


def run_app(app, host, port):
    if "DEBUG_MODE" in os.environ:
        app.run(host=host, port=port, debug=True)
    else:
        waitress.serve(app, host=host, port=port)


def get_valid_filename(folder, length=8):
    success = False

    while not success:
        rand_id = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=length)
        )
        filename = folder / f"img-{rand_id}.png"
        success = not filename.exists()

    return filename


def plot_path(locs, path, img_info=None):
    """Plot a path through locations (to make a closed loop the first and last locations should be the same)."""
    # convert the path and the locations into numpy arrays
    path = np.array([locs[j] for j in path])
    locs_array = np.array(locs)

    fig, ax = plt.subplots(
        figsize=(img_info["width"] / DPI, img_info["height"] / DPI),
        tight_layout={"pad": 0},
    )
    ax.axis("off")
    background = plt.imread(img_info["file"])
    ax.imshow(background)

    ax.plot(path[:, 0], path[:, 1])
    ax.scatter(locs_array[:, 0], locs_array[:, 1], color="red")

    img_file = get_valid_filename(IMG_FOLDER)
    fig.savefig(img_file, format="png", dpi=DPI)
    plt.close(fig)

    return img_file
