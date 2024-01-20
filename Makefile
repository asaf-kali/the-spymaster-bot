PYTHON_TEST_COMMAND=pytest -s
DEL_COMMAND=gio trash
SYNC=--sync

# Install

upgrade-pip:
	pip install --upgrade pip

install-ci: upgrade-pip
	pip install poetry==1.7.1
	poetry config virtualenvs.create false

install-run:
	poetry install --only main

install-test:
	poetry install --only main --only test

install-lint:
	poetry install --only lint

install-dev: upgrade-pip
	poetry install --no-root $(SYNC)
	pre-commit install

install: lock-check install-dev lint cover

# Poetry

lock:
	poetry lock --no-update

lock-check:
	poetry check --lock

lock-export: lock-check
	poetry export -f requirements.txt --output requirements.lock --only main --without-hashes

# Test

test:
	export ENV_FOR_DYNACONF=test; \
	export TELEGRAM_TOKEN="123:ABC"; \
	python -m $(PYTHON_TEST_COMMAND)

cover:
	export ENV_FOR_DYNACONF=test; \
	coverage run -m $(PYTHON_TEST_COMMAND)
	coverage html
	xdg-open htmlcov/index.html &
	$(DEL_COMMAND) .coverage*

# Lint

format:
	ruff . --fix
	black .
	isort .

check-ruff:
	ruff .

check-black:
	black --check .

check-isort:
	isort --check .

check-mypy:
	mypy .

check-pylint:
	pylint src/ --fail-under=10

lint: format
	pre-commit run --all-files
	@make check-pylint --no-print-directory

# Run

run:
	@make kill --no-print-directory
	python -m telegram_bot.main

kill:
	killall python || true

# Deploy

build-layer:
	./scripts/build_layer.sh

update:
	cd tf; make update;

plan:
	cd tf; make plan;

apply:
	cd tf; make apply;

deploy:
	cd tf; make deploy;

# Quick and dirty

wip:
	make format
	git add .
	git commit -m "Auto commit" --no-verify
	git push
