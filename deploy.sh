docker pull jedreky/tsp:solver_flask
docker pull jedreky/tsp:solver_fastapi
docker pull jedreky/tsp:webapp

if command -v docker-compose
then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

FRAMEWORK=fastapi ${DOCKER_COMPOSE_CMD} --env-file config.env up
