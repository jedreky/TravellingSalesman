include config.env

REGISTRY = $(AWS_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
REPO=tsp
#SOLVER_IMG_TAG := solver.$(shell git rev-parse --short HEAD)
#WEBAPP_IMG_TAG := webapp.$(shell git rev-parse --short HEAD)

SOLVER_IMG_TAG := solver
WEBAPP_IMG_TAG := webapp


.PHONY: build-solver
build-solver:
	docker build --build-arg SOLVER_PORT=$(SOLVER_PORT) --build-arg WEBAPP_PORT=$(WEBAPP_PORT) \
	--tag $(REGISTRY)/$(REPO):$(SOLVER_IMG_TAG) . \
	--file Dockerfile.solver

.PHONY: push-solver
push-solver: build-solver
	aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) \
	| docker login --username AWS --password-stdin $(REGISTRY)
	docker push $(REGISTRY)/$(REPO):$(SOLVER_IMG_TAG)

.PHONY: build-webapp
build-webapp:
	docker build --build-arg SOLVER_PORT=$(SOLVER_PORT) --build-arg WEBAPP_PORT=$(WEBAPP_PORT) \
	--tag $(REGISTRY)/$(REPO):$(WEBAPP_IMG_TAG) . \
	--file Dockerfile.webapp

.PHONY: push-webapp
push-webapp: build-webapp
	aws ecr get-login-password --region $(AWS_REGION) --profile $(AWS_PROFILE) \
	| docker login --username AWS --password-stdin $(REGISTRY)
	docker push $(REGISTRY)/$(REPO):$(WEBAPP_IMG_TAG)

.PHONY: build
build: build-solver build-webapp

.PHONY: push
push: push-solver push-webapp

.PHONY: deploy
deploy: build push
