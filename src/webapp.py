import json
import requests
import time

from flask import Flask, Markup, render_template, request

from src.utils import HOST, SOLVER_PORT, WEBAPP_PORT, IMG_FOLDER, run_app, plot_path


# minimal and maximal number of locations
MIN_LOC_NUM = 4
MAX_LOC_NUM = 16

# background image
BACKGROUND_FILE = IMG_FOLDER / "background.png"
IMG_SIZE = (960, 540)

# template file
TEMPLATE_FILE = "main.html"


app = Flask(__name__)


def get_time_string(time_elapsed):
    """Return a human-readable string containing the computation time."""
    if time_elapsed < 0.001:
        return "less than 0.01"
    else:
        return "{:.2f}".format(time_elapsed)


def call_solver(locs):
    res = requests.post(url=f"http://localhost:{SOLVER_PORT}/solve", json=locs)
    return res.json()


def generate_page(img_file, message=""):
    img_file_for_html = img_file.relative_to(*img_file.parts[:2])
    return render_template(
        TEMPLATE_FILE,
        img_file=img_file_for_html,
        img_size=IMG_SIZE,
        message=Markup(message),
    )


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        return generate_page(BACKGROUND_FILE)
    elif request.method == "POST":
        locs = json.loads(request.form["points"])
        n = len(locs)

        if n >= MIN_LOC_NUM:
            message = ""

            if n > MAX_LOC_NUM:
                locs = locs[:MAX_LOC_NUM]
                message += "You have specified a lot of points, so I have only considered the first {} of them.<br>".format(
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

            message += "Length of the shortest path: {:.1f} (size of the entire map: {} x {})<br>".format(
                sol["length"], IMG_SIZE[0], IMG_SIZE[1]
            )
            message += "Total computation time: {}s".format(time_str)
            return generate_page(img_file=img_file, message=message)
        elif n < MIN_LOC_NUM:
            return generate_page(
                img_file=img_file, message="You have not specified enough points!"
            )
    else:
        return "An error has occurred"


if __name__ == "__main__":
    run_app(app, HOST, WEBAPP_PORT)
