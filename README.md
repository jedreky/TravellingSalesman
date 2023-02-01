# To run locally

To build containers run:

```
git checkout git@github.com:jedreky/TravellingSalesman.git
make build
```

Alternatively, you can pull the containers from Dockerhub:

https://hub.docker.com/r/jedreky/tsp/tags

```
docker pull jedreky/tsp:solver_flask
docker pull jedreky/tsp:solver_fastapi
docker pull jedreky/tsp:webapp
```

Then, use, e.g.

```
FRAMEWORK=flask docker-compose --env-file config.env up
```

or

```
FRAMEWORK=fastapi docker-compose --env-file config.env up
```

## To try

http://83.229.82.229:8338/

http://83.229.82.229:8337/

http://83.229.82.229:8337/docs