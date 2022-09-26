PYTHON_TEST_COMMAND=pytest -s
DEL_COMMAND=gio trash
LINE_LENGTH=120

# Install

install-run:
	pip install --upgrade pip
	pip install -r requirements.txt

install-test:
	pip install -r requirements-test.txt
	@make install-run --no-print-directory

install-dev:
	pip install -r requirements-dev.txt
	pip install -r requirements-lint.txt
	@make install-test --no-print-directory
	pre-commit install

install: install-dev test lint

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
	black .
	isort .

check-black:
	black --check .

check-isort:
	isort --check .

check-mypy:
	mypy .

check-flake8:
	flake8 . --max-line-length=$(LINE_LENGTH) --ignore=E203,W503,E402 --exclude=local,.deployment

lint: format
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
	cd tf; make plan;

apply:
	cd tf; make apply;

update:
	cd tf; make deploy;

deploy: build-layer update
