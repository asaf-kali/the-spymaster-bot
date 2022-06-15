PYTHON_TEST_COMMAND=pytest -s
DEL_COMMAND=gio trash
LINE_LENGTH=120
TERRAFORM_PLAN_FILE=deploy.tfplan

# Install

install-run:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install the-spymaster-api.tar.gz

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
	flake8 . --max-line-length=$(LINE_LENGTH) --ignore=E203,W503,E402

lint: lint-only
	pre-commit run --all-files

# Run

run:
	@make kill --no-print-directory
	python -m telegram_bot.main

kill:
	killall python || true

# Deploy

plan:
	terraform plan -var 'telegram_token=123' -out $(TERRAFORM_PLAN_FILE)

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)

deploy:
	@make plan --no-print-directory
	@make apply --no-print-directory
