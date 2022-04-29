SHELL=/bin/bash
ECR_REGISTRY=222053980223.dkr.ecr.us-east-1.amazonaws.com
DATETIME:=$(shell date -u +%Y%m%dT%H%M%SZ)

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

### Docker commands ###
dist-dev: ## Build docker image
	docker build --platform linux/amd64 -t $(ECR_REGISTRY)/timdex-transmogrifier-dev:latest \
		-t $(ECR_REGISTRY)/timdex-transmogrifier-dev:`git describe --always` \
		-t timdex-transmogrifier-dev:latest .

publish-dev: dist-dev ## Build, tag and push
	docker login -u AWS -p $$(aws ecr get-login-password --region us-east-1) $(ECR_REGISTRY)
	docker push $(ECR_REGISTRY)/timdex-transmogrifier-dev:latest
	docker push $(ECR_REGISTRY)/timdex-transmogrifier-dev:`git describe --always`
