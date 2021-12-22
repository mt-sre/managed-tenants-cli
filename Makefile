# These shell flags are REQUIRED for an early exit in case any program called by make errors!
.SHELLFLAGS=-euo pipefail -c
SHELL := /bin/bash

TARGETS := prepare install develop check test generate release clean docker-build docker-run
.PHONY: $(TARGETS)

# Required because the image sets up a venv in Dockerfile
# https://catalog.redhat.com/software/containers/ubi8/python-39/6065b24eb92fbda3a4c65d8f?container-tabs=dockerfile
export PIPENV_VENV_IN_PROJECT=1
export PIPENV_IGNORE_VIRTUALENVS=1

CI ?= false

all:
	@echo
	@echo "Targets:"
	@echo "prepare:      Installs pipenv."
	@echo "install:      Installs the sretoolbox package and its dependencies."
	@echo "develop:      Installs the sretoolbox package, its dependencies and its development dependencies."
	@echo "check:        Runs linters and formatters."
	@echo "test:         Runs the tests."
	@echo "generate:     Generates a Markdown doc from the addon json schema."
	@echo "release:      Release the python package to pypi."
	@echo "clean:        Clean the working repository."
	@echo "docker-build: Builds the docker image locally."
	@echo "docker-run:   Run commands inside the docker image. (usage: '$ [CMD=<command>] make docker-run')"
	@echo


prepare:
	# Can't use --user inside container
	if [ "${CI}" == "true" ]; then \
		pip install pipenv --upgrade; \
	else \
		pip install pipenv --user --upgrade; \
	fi

install: prepare
	pipenv install

develop: prepare
	pipenv install --dev

clean:
	pipenv --rm || true
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

LINTERS := $(shell pwd)/.linters
PY_SRCS := managedtenants/ hack/ tests/ setup.py
pylint:
	pipenv run pylint --rcfile=$(LINTERS)/pylint $(PY_SRCS)

check: pylint
	pipenv run black --config=$(LINTERS)/black --experimental-string-processing $(PY_SRCS) && \
	pipenv run isort --profile black -l 80 $(PY_SRCS) && \
	pipenv run flake8 --config=$(LINTERS)/flake8 $(PY_SRCS) && \
	pipenv run yamllint --config-file=$(LINTERS)/yamllint .

test:
	pipenv run pytest --cache-clear -v tests/

release:
	python -m pip install twine wheel
	python setup.py bdist_wheel
	python -m twine upload dist/*

generate: generate-md-schema pre-commit-autoupdate

SCHEMA_IN := $(PWD)/managedtenants/data/metadata.schema.yaml
MARKDOWN_OUT := $(PWD)/docs/tenants/zz_schema_generated.md
IMAGESET_SCHEMA_IN :=  $(PWD)/managedtenants/data/imageset.schema.yaml
IMAGESET_MARKDOWN_OUT := $(PWD)/docs/tenants/zz_imageset_schema_generated.md
generate-md-schema: develop
	pipenv run python $(PWD)/hack/yamlschema2md.py --schema $(SCHEMA_IN) --output $(MARKDOWN_OUT)
	pipenv run python $(PWD)/hack/yamlschema2md.py --schema $(IMAGESET_SCHEMA_IN) --output $(IMAGESET_MARKDOWN_OUT)

pre-commit-autoupdate: develop
	pipenv run pre-commit autoupdate

DEV_IMAGE := managedtenants_cli:dev
docker-build:
	docker build -t $(DEV_IMAGE) -f Dockerfile.test .

CMD := check
docker-run: docker-build
	docker run --rm -it --name managedtenants_cli-dev -v "/var/run/docker.sock:/var/run/docker.sock" $(DEV_IMAGE) $(CMD)
