.DEFAULT_GOAL:=help

.PHONY: dev
dev: ## Install adapter in editable mode with development dependencies
	pip install -e . -r dev-requirements.txt && pre-commit install

.PHONY: dev-uninstall
dev-uninstall: ## Uninstall all packages while maintaining the virtual environment
	pip freeze | grep -v "^-e" | cut -d "@" -f1 | xargs pip uninstall -y
	pip uninstall -y dbt-mariadb

.PHONY: mypy
mypy: ## Run mypy against staged changes
	pre-commit run --hook-stage manual mypy-check | grep -v "INFO"

.PHONY: flake8
flake8: ## Run flake8 against staged changes
	pre-commit run --hook-stage manual flake8-check | grep -v "INFO"

.PHONY: black
black: ## Run black against staged changes
	pre-commit run --hook-stage manual black-check -v | grep -v "INFO"

.PHONY: lint
lint: ## Run flake8 and mypy
	pre-commit run flake8-check --hook-stage manual | grep -v "INFO"
	pre-commit run mypy-check --hook-stage manual | grep -v "INFO"

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
test-all: test-unit test-functional ## Run unit and 11.4 functional tests

.PHONY: clean
clean: ## Remove untracked files
	git clean -f -X

.PHONY: help
help: ## Show this help message
	@echo 'usage: make [target]'
	@echo
	@echo 'targets:'
	@grep -E '^[7+a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
