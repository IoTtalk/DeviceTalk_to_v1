ENVFILE=./.env
DJANGO_ENVFILE=./_/env/.env
ifneq (,$(wildcard ${ENVFILE}))
include ${ENVFILE}
endif

CP_CMD=cp -n
SED_CMD=sed -i
ifeq ($(OS),Windows_NT)
	$(error This make script will not support Windows OS.)
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Darwin)
		SED_CMD=sed -i ''
	endif
endif

VOLUME_SET=-v `pwd`/${DJANGO_ENV_PATH}:/devicetalk/_/env/.env -v `pwd`/$(DATA_PATH):/devicetalk/datas -v `pwd`/DeviceTalk-Basic-file:/devicetalk/DeviceTalk-Basic-file -v `pwd`/DeviceTalk-Library-file:/devicetalk/DeviceTalk-Library-file
DOCKER_RUN_CMD=docker run $(VOLUME_SET) -it devicetalk:${USER}
DOCKER_COMPOSE_CMD=

ifndef DOCKER_COMPOSE_CMD
ifneq (,$(if $(shell which docker),$(findstring Docker Compose,$(shell docker info -f '{{ .ClientInfo.Plugins }}'))))
  DOCKER_COMPOSE_CMD=docker compose
else ifneq (,$(shell which docker-compose))
  DOCKER_COMPOSE_CMD=docker-compose
else
  DOCKER_COMPOSE_CMD=$(error Could not find either `docker compose` plugin or `docker-compose` command)
endif
endif

config:
ifeq (,$(wildcard ${DJANGO_ENVFILE}))
	$(CP_CMD) ./_/env/.env.sample ${DJANGO_ENVFILE};
else
	@echo "DJANGO_ENVFILE ${DJANGO_ENVFILE} already exists, skipping";
endif
.PHONY: config

dockerconfig:
ifeq (,$(wildcard ${ENVFILE}))
	$(CP_CMD) ./share/.env.sample ${ENVFILE};
else
	@echo "ENVFILE ${ENVFILE} already exists, skipping"
endif
	@read -p "Which port do you want to use in host? " HOST_PORT; \
	$(SED_CMD) -e 's@^HOST_PORT=.*$$@HOST_PORT='$$HOST_PORT'@' ${ENVFILE};
.PHONY: dockerconfig

submodule:
.PHONY: submodule

build:
	$(DOCKER_COMPOSE_CMD) build devicetalk
.PHONY: build

up:
	$(DOCKER_COMPOSE_CMD) up
.PHONY: up

initdb: migrate
	git submodule init
	git submodule update --recursive
	$(DOCKER_RUN_CMD) python manage.py initdb
.PHONY: initdb

migrate:
	$(DOCKER_RUN_CMD) python manage.py migrate
.PHONY: initdb

shell:
	$(DOCKER_RUN_CMD) python manage.py shell
.PHONY: shell

bash:
	$(DOCKER_RUN_CMD) bash
.PHONY: bash

logs:
	$(DOCKER_COMPOSE_CMD) logs -f devicetalk
.PHONY: logs

down:
	$(DOCKER_COMPOSE_CMD) down
.PHONY: down
