from flask import Flask, request

from src.solver_core import TSP
from src.utils import SOLVER_PORT, run_app


app = Flask(__name__)


@app.route("/solve", methods=["POST"])
def solve():
    coords = request.get_json()["coords"]
    return TSP(coords=coords).solve()


if __name__ == "__main__":
    run_app(app, SOLVER_PORT)
