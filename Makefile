SHELL=/bin/bash
DATETIME:=$(shell date -u +%Y%m%dT%H%M%SZ)

### This is the Terraform-generated header for transmogrifier-dev. ###
ECR_NAME_DEV := transmogrifier-dev
ECR_URL_DEV := 222053980223.dkr.ecr.us-east-1.amazonaws.com/transmogrifier-dev
CPU_ARCH ?= $(shell cat .aws-architecture 2>/dev/null || echo "linux/amd64")
### End of Terraform-generated header ###

help: # Preview Makefile commands
	@awk 'BEGIN { FS = ":.*#"; print "Usage:  make <target>\n\nTargets:" } \
/^[-_[:alpha:]]+:.?*#/ { printf "  %-15s%s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: help install venv update test coveralls lint lint-fix security transform dist-dev publish-dev dist-stage publish-stage

##############################################
# Python Environment and Dependency commands
##############################################

install: .venv .git/hooks/pre-commit .git/hooks/pre-push # Install Python dependencies
	uv sync --dev

.venv:
	@echo "Creating virtual environment at .venv..."
	uv venv .venv

.git/hooks/pre-commit:
	@echo "Installing pre-commit commit hooks..."
	uv run pre-commit install --hook-type pre-commit

.git/hooks/pre-push:
	@echo "Installing pre-commit push hooks..."
	uv run pre-commit install --hook-type pre-push

venv: .venv

update: # Update Python dependencies
	uv lock --upgrade
	uv sync --dev

######################
# Unit test commands
######################

test: # Run tests and print a coverage report
	uv run coverage run --source=transmogrifier -m pytest -vv
	uv run coverage report -m

coveralls: test # Write coverage data to an LCOV report
	uv run coverage lcov -o ./coverage/lcov.info

####################################
# Code linting and formatting
####################################

lint: # Run linting, alerts only, no code changes
	uv run ruff format --diff
	uv run mypy .
	uv run ruff check .

lint-fix: # Run linting, auto fix behaviors where supported
	uv run ruff format .
	uv run ruff check --fix .

security: # Run security / vulnerability checks
	uv run pip-audit

####################################
# CLI Command
####################################

transform: # CLI without any arguments, utilizing uv script entrypoint
	uv run transform

####################################
# Container Build and Deploy
####################################

dist-dev: # Build docker container (intended for developer-based manual build)
	docker buildx build --platform $(CPU_ARCH) \
	    -t $(ECR_URL_DEV):latest-$(shell echo $(CPU_ARCH) | cut -d'/' -f2) \
	    -t $(ECR_URL_DEV):make-latest-$(shell echo $(CPU_ARCH) | cut -d'/' -f2) \
	    -t $(ECR_URL_DEV):make-$(shell git describe --always) \
	    -t $(ECR_NAME_DEV):latest .

publish-dev: dist-dev # Build, tag and push (intended for developer-based manual publish)
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(ECR_URL_DEV)
	docker push $(ECR_URL_DEV):latest-$(shell echo $(CPU_ARCH) | cut -d'/' -f2)
	docker push $(ECR_URL_DEV):make-latest-$(shell echo $(CPU_ARCH) | cut -d'/' -f2)
	docker push $(ECR_URL_DEV):make-$(shell git describe --always)

dist-stage: # Only use in an emergency
	docker buildx build --platform $(CPU_ARCH) \
	    -t $(ECR_URL_STAGE):latest-$(shell echo $(CPU_ARCH) | cut -d'/' -f2) \
	    -t $(ECR_URL_STAGE):make-latest-$(shell echo $(CPU_ARCH) | cut -d'/' -f2) \
	    -t $(ECR_URL_STAGE):make-$(shell git describe --always) .

publish-stage: dist-stage # Only use in an emergency
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(ECR_URL_STAGE)
	docker push $(ECR_URL_STAGE):latest-$(shell echo $(CPU_ARCH) | cut -d'/' -f2)
	docker push $(ECR_URL_STAGE):make-latest-$(shell echo $(CPU_ARCH) | cut -d'/' -f2)
	docker push $(ECR_URL_STAGE):make-$(shell git describe --always)

