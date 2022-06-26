PYTHON_TEST_COMMAND=pytest -s
DEL_COMMAND=gio trash
LINE_LENGTH=120

# Install

install-run:
	pip install --upgrade pip
	pip install -r requirements.txt

install-test:
	@make install-run --no-print-directory
	pip install -r requirements-dev.txt

install-dev:
	@make install-test --no-print-directory
	pre-commit install

install: install-dev test lint

# Test

test:
	export ENV_FOR_DYNACONF=test; python -m $(PYTHON_TEST_COMMAND)

cover:
	export ENV_FOR_DYNACONF=test; coverage run -m $(PYTHON_TEST_COMMAND)
	coverage html
	xdg-open htmlcov/index.html &
	$(DEL_COMMAND) .coverage*

# Lint

lint-only:
	black .
	isort .

lint-check:
	black . --check
	isort . --check
	mypy .
	flake8 . --max-line-length=$(LINE_LENGTH) --ignore=E203,W503,E402 --exclude=local,.deployment

lint: lint-only
	pre-commit run --all-files

# Run

run:
	@make kill --no-print-directory
	python -m telegram_bot.main

kill:
	killall python || true

# Deploy

build-layer:
	sudo ./scripts/build_layer.sh

plan:
	cd tf_service; make plan;

apply:
	cd tf_service; make apply;

update:
	cd tf_service; make deploy;

deploy: build-layer update
