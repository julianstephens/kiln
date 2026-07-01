SHELL := /usr/bin/env bash

PYTHON_DIR := python
TOOLS_DIR := devtools
GO_DIR := go
DIST_DIR := dist

RUFF ?= uv run --package kiln-sdk ruff --config kiln/pyproject.toml
GO ?= go
GOLANGCI_LINT ?= golangci-lint

default: check

.PHONY: \
	help \
	format format-python format-go \
	format-check format-check-python format-check-go \
	lint lint-python lint-go \
	test test-python test-go \
	build build-python build-go \
	validate-schemas \
	generate generate-python generate-go \
	clean check 

help:
	@printf '%s\n' \
		"Kiln development commands:" \
		"" \
		"  make format            Format all Python and Go code" \
		"  make format-check      Verify formatting without modifying files" \
		"  make lint              Lint all Python and Go code" \
		"  make test              Run all tests" \
		"  make build             Build Python and Go artifacts" \
		"  make validate-schemas  Validate JSON schemas" \
		"  make generate          Generate models from JSON schemas" \
		"  make clean             Remove generated build artifacts"

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

format: format-python format-go

format-python:
	cd $(PYTHON_DIR) && $(RUFF) format .
	cd $(PYTHON_DIR) && $(RUFF) check --fix .

format-go:
	cd $(GO_DIR) && $(GOLANGCI_LINT) fmt ./...

format-check: format-check-python format-check-go

format-check-python:
	cd $(PYTHON_DIR) && $(RUFF) format --check .

format-check-go:
	cd $(GO_DIR) && $(GOLANGCI_LINT) fmt --diff ./...

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------

lint: lint-python lint-go

lint-python:
	cd $(PYTHON_DIR) && $(RUFF) check .

lint-go:
	cd $(GO_DIR) && $(GOLANGCI_LINT) run ./...

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: test-python test-go

test-python:
	cd $(PYTHON_DIR) && uv sync --package kiln-sdk && uv run pytest -c kiln/pyproject.toml 

test-go:
	cd $(GO_DIR) && $(GO) test -v ./...

# ---------------------------------------------------------------------------
# Builds
# ---------------------------------------------------------------------------

build: build-python build-go

build-python:
	rm -rf $(DIST_DIR)/python
	mkdir -p $(DIST_DIR)/python
	uv build \
		--out-dir "$(CURDIR)/$(DIST_DIR)/python"

build-go:
	rm -rf $(DIST_DIR)/bin
	mkdir -p $(DIST_DIR)/bin
	cd $(GO_DIR) && \
		$(GO) build \
			-o "$(CURDIR)/$(DIST_DIR)/bin/kiln-runtime" \
			./cmd/kiln-runtime

# ---------------------------------------------------------------------------
# Validate JSON Schemas
# ---------------------------------------------------------------------------
validate-schemas:
	uv run python $(TOOLS_DIR)/schema_tools/validate.py

# ---------------------------------------------------------------------------
# Generate models from JSON Schemas
# ---------------------------------------------------------------------------
generate-check: generate
	git diff --exit-code python/kiln/schemas
	git diff --exit-code go/schema

generate: generate-python generate-go

generate-python:
	uv run generatepymodels

generate-go:
	uv run generategomodels

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean:
	rm -rf $(DIST_DIR)
	rm -rf $(PYTHON_DIR)/build
	rm -rf $(PYTHON_DIR)/*.egg-info
	find $(PYTHON_DIR) \
		-type d \
		\( -name __pycache__ -o -name .ruff_cache \) \
		-prune \
		-exec rm -rf {} +

check: format-check lint test build	validate-schemas generate-check