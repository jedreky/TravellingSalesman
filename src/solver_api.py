from flask import Flask, request

from src.solver import TSP
from src.utils import HOST, SOLVER_PORT, run_app

app = Flask(__name__)


@app.route("/solve", methods=["POST"])
def solve():
    coords = request.get_json()
    problem = TSP(coords=coords)
    solution = problem.solve()
    return solution.to_json()


if __name__ == "__main__":
    run_app(app, HOST, SOLVER_PORT)
