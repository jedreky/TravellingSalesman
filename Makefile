include aws_config.env

REGISTRY = $(AWS_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
REPO=tsp
#SOLVER_IMG_TAG := $(REPO):solver.$(shell git rev-parse --short HEAD)
#WEBAPP_IMG_TAG := $(REPO):webapp.$(shell git rev-parse --short HEAD)

SOLVER_IMG_TAG := $(REPO):solver
WEBAPP_IMG_TAG := $(REPO):webapp


.PHONY: build-solver_flask
build-solver_flask:
	docker build --tag $(SOLVER_IMG_TAG)_flask . --file Dockerfile.solver_flask

.PHONY: build-solver_fastapi
build-solver_fastapi:
	docker build --tag $(SOLVER_IMG_TAG)_fastapi . --file Dockerfile.solver_fastapi

.PHONY: push-solver
push-solver: build-solver
	aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) \
	| docker login --username AWS --password-stdin $(REGISTRY)
	docker tag $(SOLVER_IMG_TAG) $(REGISTRY)/$(SOLVER_IMG_TAG)
	docker push $(REGISTRY)/$(SOLVER_IMG_TAG)

.PHONY: build-webapp
build-webapp:
	docker build --tag $(WEBAPP_IMG_TAG) . --file Dockerfile.webapp

.PHONY: push-webapp
push-webapp: build-webapp
	aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) \
	| docker login --username AWS --password-stdin $(REGISTRY)
	docker tag $(WEBAPP_IMG_TAG) $(REGISTRY)/$(WEBAPP_IMG_TAG)
	docker push $(REGISTRY)/$(WEBAPP_IMG_TAG)

.PHONY: build
build: build-solver_flask build-solver_fastapi build-webapp

.PHONY: push
push: push-solver push-webapp

.PHONY: deploy
deploy: build push