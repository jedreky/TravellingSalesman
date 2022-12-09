ifneq (,$(wildcard ./.env))
	include .env
	export
endif

REGISTRY = $(AWS_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
REPO=tsp
IMG_TAG := solver.$(shell git rev-parse --short HEAD)

.PHONY: build-solver
build-solver:
	docker build --build-arg SOLVER_PORT=$(SOLVER_PORT) \
	--tag $(REGISTRY)/$(REPO):$(IMG_TAG) . \
	--file Dockerfile.solver

.PHONY: push-solver
push-solver: build-solver
	aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) \
	| docker login --username AWS --password-stdin $(REGISTRY)
	docker push $(REGISTRY)/$(REPO):$(IMG_TAG)
