from flask import Flask, request
import os
import waitress

from src.solver import TSP

app = Flask(__name__)


@app.route("/solve", methods=["POST"])
def solve():
    coords = request.get_json()
    problem = TSP(coords=coords)
    solution = problem.solve()
    return solution.to_json()


if __name__ == "__main__":
    port = 8080

    if "DEBUG_MODE" in os.environ:
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        waitress.serve(app, host="0.0.0.0", port=port)
