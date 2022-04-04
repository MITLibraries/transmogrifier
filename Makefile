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
	pipenv run pytest --cov=transmogrifier