# Makefile for common-file-generator.
# All commands run through uv so they use the project virtualenv.

UV ?= uv
HOST ?= 127.0.0.1
PORT ?= 18990
IMAGE ?= common-file-generator:local

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Sync core + dev dependencies
	$(UV) sync

.PHONY: install-web
install-web: ## Sync with the optional web UI extra
	$(UV) sync --extra web

.PHONY: hooks
hooks: ## Install pre-commit git hooks
	$(UV) run pre-commit install

.PHONY: serve
serve: install-web ## Run the web UI (HOST/PORT overridable)
	$(UV) run gen-ui --host $(HOST) --port $(PORT)

.PHONY: deck
deck: ## Generate a sample 70-slide maximum deck into output/
	$(UV) run generate deck --out output/deck.pptx --complexity maximum --slides 70

.PHONY: doc
doc: ## Generate a sample 20-section maximum Word document into output/
	$(UV) run generate doc --out output/document.docx --complexity maximum --sections 20

.PHONY: sheet
sheet: ## Generate a sample 5-sheet maximum Excel workbook into output/
	$(UV) run generate sheet --out output/workbook.xlsx --complexity maximum --sheets 5

.PHONY: test
test: ## Run the test suite
	$(UV) run pytest

.PHONY: lint
lint: ## Lint with ruff
	$(UV) run ruff check .

.PHONY: format
format: ## Format with ruff
	$(UV) run ruff format .

.PHONY: check
check: lint test ## Lint then test

.PHONY: pre-commit
pre-commit: ## Run all pre-commit hooks on all files
	$(UV) run pre-commit run --all-files

.PHONY: build
build: ## Build the wheel
	$(UV) build --wheel

.PHONY: docker-build
docker-build: ## Build the container image
	docker build -t $(IMAGE) .

.PHONY: docker-up
docker-up: ## Build and run the service in the foreground (UI + API on PORT)
	docker compose up --build

.PHONY: docker-down
docker-down: ## Stop and remove the running service
	docker compose down

.PHONY: clean
clean: ## Remove build artifacts and caches
	rm -rf dist build output
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
	find . -type d -name '.ruff_cache' -prune -exec rm -rf {} +
