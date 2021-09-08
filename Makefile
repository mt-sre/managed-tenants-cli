SHELL=/bin/bash
.SHELLFLAGS=-euo pipefail -c

TARGETS := help \
		   init requirements-dev develop clean _clean-build _clean-py \
		   lint fmt test \
		   check build-deploy \
		   generate generate-md-schema
.PHONY: $(TARGETS)

VENV := $(PWD)/venv
BIN := $(VENV)/bin

##@ General

help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)


##@ Development

init: ## Initialize the virtual environment if needed
	if [ ! -d "$(VENV)" ]; then python3 -m venv $(VENV); fi

requirements-dev: init ## Installs python requirements-dev
	$(info Installing python requirements-dev...)
	$(BIN)/pip install -r requirements-dev.txt > /dev/null 2>&1


develop: requirements-dev ## Installs the requirements-dev and the package in develop mode
	$(info Installing managedtenants package...)
	$(BIN)/python setup.py develop > /dev/null 2>&1

clean: _clean-build _clean-py ## Cleans directory and venv
	@rm -rf $(VENV)

_clean-build:
	@rm -fr build/
	@rm -fr dist/
	@rm -fr .eggs/
	@find . -name '*.egg-info' -not -path "./venv/*" -exec rm -fr {} +
	@find . -name '*.egg' -not -path "./venv/*" -exec rm -f {} +

_clean-py:
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +
	@rm -fr .pytest_cache

##@ Linting & Testing

LINTERS := $(PWD)/.linters
PY_SRCS := managedtenants/ setup.py
# Needs to fully source the venv because pylint validates imports
lint: develop ## Runs flake8, pylint and yamllint
	@. $(VENV)/bin/activate && \
	flake8 --config=$(LINTERS)/flake8 $(PY_SRCS) && \
	pylint --rcfile=$(LINTERS)/pylint $(PY_SRCS) && \
	yamllint --config-file=$(LINTERS)/yamllint .

fmt: requirements-dev ## Formats python files with black
	$(BIN)/black --config=$(LINTERS)/black --experimental-string-processing $(PY_SRCS)

test: clean develop ## Cleans cache and runs test suite using Pytest
	$(BIN)/pytest --cache-clear -v tests

##@ Build & Deploy

ENVIRONMENTS := stage integration production
check: develop ## Runs the style check, the code check and all the tasks in dry-run mode
	for task_type in check deploy; do \
		for env in $(ENVIRONMENTS); do \
			$(BIN)/managedtenants --environment=$${env} run --dry-run tasks/$${task_type}/ ; \
		done \
	done

build-deploy: develop ## Runs the 'deploy' tasks in debug mode
	for env in $(ENVIRONMENTS); do \
		$(BIN)/managedtenants --environment=$${env} run --debug tasks/deploy/ ; \
	done

##@ Generators

generate: generate-md-schema

SCHEMA_IN := $(PWD)/managedtenants/data/metadata.schema.yaml
MARKDOWN_OUT := $(PWD)/docs/tenants/zz_schema_generated.md
generate-md-schema: requirements-dev ## Generates a Markdown doc from the addon json schema.
	$(BIN)/python $(PWD)/hack/yamlschema2md.py --schema $(SCHEMA_IN) --output $(MARKDOWN_OUT)
