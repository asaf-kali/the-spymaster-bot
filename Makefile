PYTHON_TEST_COMMAND=pytest -s
DEL_COMMAND=gio trash

# Install

upgrade-pip:
	pip install --upgrade pip

install-run:
	pip install -r requirements.txt

install-test:
	pip install -r requirements-test.txt
	@make install-run --no-print-directory

install-lint:
	pip install -r requirements-lint.txt

install-dev: upgrade-pip
	pip install -r requirements-dev.txt
	@make install-lint --no-print-directory
	@make install-test --no-print-directory
	pre-commit install

install: install-dev lint cover

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
	sudo ./scripts/build_layer.sh

plan:
	cd tf; make plan;

apply:
	cd tf; make apply;

update:
	cd tf; make deploy;

deploy: build-layer update
