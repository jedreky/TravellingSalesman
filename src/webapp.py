import json
import random
import string
import time

import matplotlib.pyplot as plt
import numpy as np
import requests
from flask import Flask, Markup, render_template, request

from src.utils import GITHUB_URL, IMG_FOLDER, SOLVER_PORT, WEBAPP_PORT, run_app

DPI = 100

# minimal and maximal number of locations
MIN_LOC_NUM = 4
MAX_LOC_NUM = 16

# background image
BACKGROUND_FILE = IMG_FOLDER / "background.png"
IMG_SIZE = (960, 540)

# template file
TEMPLATE_FILE = "main.html"


assert WEBAPP_PORT is not None, "Error: webapp port not set"


app = Flask(__name__)


def get_time_string(time_elapsed):
    """Return a human-readable string containing the computation time."""
    if time_elapsed < 0.001:
        return "less than 0.01"
    else:
        return "{:.2f}".format(time_elapsed)


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


def call_solver(locs):
    res = requests.post(url=f"http://solver:{SOLVER_PORT}/solve", json={"coords": locs})
    return res.json()


def generate_page(img_file, desc=""):
    img_file_for_html = img_file.relative_to(*img_file.parts[:2])

    footer = f'Check out the source code at <a href="{GITHUB_URL}">GitHub</a>!'

    framework = os.environ.get("FRAMEWORK", None)

    if framework is not None:
        footer += f"Using {framework} endpoint"

    return render_template(
        TEMPLATE_FILE,
        img_file=img_file_for_html,
        img_size=IMG_SIZE,
        desc=Markup(desc),
        footer=Markup(footer),
    )


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        return generate_page(BACKGROUND_FILE)
    elif request.method == "POST":
        locs = json.loads(request.form["points"])
        n = len(locs)

        if n >= MIN_LOC_NUM:
            desc = ""

            if n > MAX_LOC_NUM:
                locs = locs[:MAX_LOC_NUM]
                desc += "You have specified a lot of points, so let me just consider the first {} of them.<br>".format(
                    MAX_LOC_NUM
                )

            t0 = time.time()
            sol = call_solver(locs)
            time_str = get_time_string(time.time() - t0)

            img_info = {
                "file": BACKGROUND_FILE,
                "width": IMG_SIZE[0],
                "height": IMG_SIZE[1],
            }
            img_file = plot_path(locs, sol["path"], img_info)

            desc += "Length of the shortest path: {:.1f} (size of the entire map: {} x {})<br>".format(
                sol["length"], IMG_SIZE[0], IMG_SIZE[1]
            )
            desc += "Total computation time: {}s".format(time_str)
            return generate_page(img_file=img_file, desc=desc)
        elif n < MIN_LOC_NUM:
            return generate_page(
                img_file=BACKGROUND_FILE, desc="You have not specified enough points!"
            )
    else:
        return "An error has occurred"


if __name__ == "__main__":
    run_app(app, WEBAPP_PORT)
