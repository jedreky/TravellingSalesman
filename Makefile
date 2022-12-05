IMG_NAME := "tsp_solver"
GITCOMMIT := $(shell git rev-parse --short HEAD)

.PHONY: build-solver
build-solver:
	docker build -t $(IMG_NAME):$(GITCOMMIT) . --file Dockerfile.solver
