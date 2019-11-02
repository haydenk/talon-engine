BASE := $(shell /bin/pwd)
CODE_COVERAGE = 72
PIPENV ?= pipenv

build: clean install test lint
	$(PIPENV) run sam build

clean: pyenv
	-rm -rfv .aws-sam .pytest_cache

pyenv:
	@test -s $(PWD)/.python-version || { echo ".python-version file does not exist! Exiting..."; exit 1; }

shell: pyenv
	@$(PIPENV) shell

install: pyenv ##=> Install dependencies
	$(PIPENV) install --dev

test: pyenv ##=> Run pytest
	$(PIPENV) run python -m pytest --disable-pytest-warnings --cov $(BASE) --cov-report term-missing --cov-fail-under $(CODE_COVERAGE) tests/ -v

lint: pyenv ##=> Run pylint
	$(PIPENV) run python -m pylint --rcfile=.pylintrc *
