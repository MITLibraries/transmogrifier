SHELL=/bin/bash
DATETIME:=$(shell date -u +%Y%m%dT%H%M%SZ)
### This is the Terraform-generated header for transmogrifier-dev
ECR_NAME_DEV:=transmogrifier-dev
ECR_URL_DEV:=222053980223.dkr.ecr.us-east-1.amazonaws.com/transmogrifier-dev
### End of Terraform-generated header ###

lint: bandit black flake8 isort mypy

bandit:
	pipenv run bandit -r transmogrifier

black:
	pipenv run black --check --diff transmogrifier tests

coveralls: test
	pipenv run coveralls

flake8:
	pipenv run flake8 transmogrifier tests

install:
	pipenv install --dev

isort:
	pipenv run isort transmogrifier tests --diff

mypy:
	pipenv run mypy transmogrifier

test:
	pipenv run pytest --cov-report term-missing --cov=transmogrifier

### Developer Deploy Commands ###
dist-dev: ## Build docker container (intended for developer-based manual build)
	docker build --platform linux/amd64 \
	    -t $(ECR_URL_DEV):latest \
		-t $(ECR_URL_DEV):`git describe --always` \
		-t $(ECR_NAME_DEV):latest .

publish-dev: dist-dev ## Build, tag and push (intended for developer-based manual publish)
	docker login -u AWS -p $$(aws ecr get-login-password --region us-east-1) $(ECR_URL_DEV)
	docker push $(ECR_URL_DEV):latest
	docker push $(ECR_URL_DEV):`git describe --always`
