PYTHON_TEST_COMMAND=pytest -s
DEL_COMMAND=gio trash
LINE_LENGTH=120
TERRAFORM_PLAN_FILE=deploy.tfplan
DEPLOYMENT_DIR=.deployment
LAMBDA_ZIP_FILE=the-spymaster-bot.zip
LAYER_ZIP_FILE=the-spymaster-bot-layer.zip

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
	python -m $(PYTHON_TEST_COMMAND)

cover:
	coverage run -m $(PYTHON_TEST_COMMAND)
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
	terraform plan -var 'telegram_token=123' -out $(TERRAFORM_PLAN_FILE)

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)

deploy:
	@make build-layer --no-print-directory
	@make plan --no-print-directory
	@make apply --no-print-directory
	$(DEL_COMMAND) $(LAMBDA_ZIP_FILE) $(LAYER_ZIP_FILE)
