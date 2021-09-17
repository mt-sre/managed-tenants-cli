all:
	@echo
	@echo "Targets:"
	@echo "prepare:      Installs pipenv."
	@echo "install:      Installs the sretoolbox package and its dependencies."
	@echo "develop:      Installs the sretoolbox package, its dependencies and its development dependencies."
	@echo "check:        Runs the style check, the code check and the tests."
	@echo "generate:     Generates a Markdown doc from the addon json schema."
	@echo


prepare:
	pip install pipenv --user --upgrade

install: prepare
	pipenv install

develop: prepare
	pipenv lock --pre --clear
	pipenv install --dev

LINTERS := $(shell pwd)/.linters
PY_SRCS := managedtenants/ setup.py
check:
	pipenv run flake8 --config=$(LINTERS)/flake8 $(PY_SRCS) && \
	pipenv run pylint --rcfile=$(LINTERS)/pylint $(PY_SRCS) && \
	pipenv run black --config=$(LINTERS)/black --experimental-string-processing $(PY_SRCS)
	pipenv run yamllint --config-file=$(LINTERS)/yamllint .

test:
	pipenv run pytest --cache-clear -v tests/

generate: generate-md-schema

SCHEMA_IN := $(PWD)/managedtenants/data/metadata.schema.yaml
MARKDOWN_OUT := $(PWD)/docs/tenants/zz_schema_generated.md
generate-md-schema: develop
	$(BIN)/python $(PWD)/hack/yamlschema2md.py --schema $(SCHEMA_IN) --output $(MARKDOWN_OUT)

test:
	@echo "hello"
