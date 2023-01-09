import os
from pathlib import Path

import waitress

SOLVER_PORT = os.environ.get("SOLVER_PORT", None)
WEBAPP_PORT = os.environ.get("WEBAPP_PORT", None)

assert SOLVER_PORT is not None, "Error: solver port not set"

AWS_EKS_ENV_VAR = "AWS_EKS"
HISTORY_MODE = AWS_EKS_ENV_VAR in os.environ and os.environ[AWS_EKS_ENV_VAR] == "1"


IMG_FOLDER = Path("src/static/imgs")


def run_app(app, port):
    if "DEBUG_MODE" in os.environ:
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        waitress.serve(app, host="0.0.0.0", port=port)
