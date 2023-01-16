include config.env
include ssh.env


.PHONY: build-solver_flask
build-solver_flask:
	docker build --tag $(SOLVER_FLASK_IMG_TAG) . --file Dockerfile.solver_flask

.PHONY: build-solver_fastapi
build-solver_fastapi:
	docker build --tag $(SOLVER_FASTAPI_IMG_TAG) . --file Dockerfile.solver_fastapi

.PHONY: push-solvers
push-solvers: build-solver_flask build-solver_fastapi
	docker push $(SOLVER_FLASK_IMG_TAG)
	docker push $(SOLVER_FASTAPI_IMG_TAG)

.PHONY: build-webapp
build-webapp:
	docker build --tag $(WEBAPP_IMG_TAG) . --file Dockerfile.webapp

.PHONY: push-webapp
push-webapp: build-webapp
	docker push $(WEBAPP_IMG_TAG)


.PHONY: build
build: build-solver_flask build-solver_fastapi build-webapp

.PHONY: push
push: push-solvers push-webapp

.PHONY: send-files-to-remote-host
send-files-to-remote-host:
	scp -P $(REMOTE_PORT) config.env $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_PATH)
	scp -P $(REMOTE_PORT) deploy.sh $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_PATH)
	scp -P $(REMOTE_PORT) docker-compose.yml $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_PATH)
