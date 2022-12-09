import os
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


HOST = "0.0.0.0"


def run_app(app, host, port):
    if "DEBUG_MODE" in os.environ:
        app.run(host=host, port=port, debug=True)
    else:
        waitress.serve(app, host=host, port=port)
