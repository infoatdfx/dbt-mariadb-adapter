.DEFAULT_GOAL:=help

.PHONY: dev
dev: ## Install adapter editable with all dev/test/lint deps
	pip install -e '.[dev]' && pre-commit install

.PHONY: dev-uninstall
dev-uninstall: ## Uninstall all packages while keeping the venv
	pip freeze | grep -v "^-e" | cut -d "@" -f1 | xargs pip uninstall -y
	pip uninstall -y dbt-mariadb

.PHONY: lint
lint: ## Run ruff + mypy
	ruff check dbt tests
	ruff format --check dbt tests
	mypy dbt

.PHONY: format
format: ## Reformat code with ruff
	ruff check --fix dbt tests
	ruff format dbt tests

.PHONY: test-unit
test-unit: ## Run unit tests
	pytest tests/unit -v

.PHONY: test-functional
test-functional: ## Run functional tests against MariaDB 11.4
	DBT_MARIADB_PORT=$${DBT_MARIADB_PORT:-3307} pytest tests/functional -v

.PHONY: test-functional-118
test-functional-118: ## Run functional tests against MariaDB 11.8 (best effort)
	DBT_MARIADB_PORT=$${DBT_MARIADB_118_PORT:-3308} pytest tests/functional -v

.PHONY: test-all
test-all: test-unit test-functional ## Unit + 11.4 functional

.PHONY: build
build: ## Build sdist + wheel
	python -m build

.PHONY: clean
clean: ## Remove untracked files
	git clean -f -X

.PHONY: help
help: ## Show this help
	@echo 'usage: make [target]'
	@echo
	@echo 'targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
