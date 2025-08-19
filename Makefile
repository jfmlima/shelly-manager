.PHONY: help install install-dev clean lint format test test-core test-api test-cli test-web test-coverage run-api run-cli setup ci-test

# Default target
help:
	@echo "Shelly Manager - Development Commands (uv-powered)"
	@echo ""
	@echo "Installation:"
	@echo "  install       Install all packages with uv"
	@echo "  install-dev   Install all packages with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  clean         Clean build artifacts and caches"
	@echo "  lint          Run linting (black, ruff, mypy)"
	@echo "  format        Format code with black and ruff"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests for all packages"
	@echo "  test-core     Run tests for core package only"
	@echo "  test-api      Run tests for api package only"
	@echo "  test-cli      Run tests for cli package only"
	@echo "  test-web      Run tests for web package only"
	@echo "  test-coverage Run all tests with coverage"
	@echo ""
	@echo "Run:"
	@echo "  run-api       Start the API server"
	@echo "  run-cli       Run CLI with help"

# Installation commands using uv
install:
	uv sync --no-dev

install-dev:
	uv sync

# Development commands
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml uv.lock
	rm -rf packages/*/build/ packages/*/dist/ packages/*/htmlcov*/

format:
	uv run black packages/
	uv run ruff check --fix packages/

lint:
	uv run black --check packages/
	uv run ruff check packages/
	uv run mypy packages/core/src/core
	uv run mypy packages/api/src/api
	uv run mypy packages/cli/src/cli

lint-web:
	@echo "Running web linting..."
	cd packages/web && npm run lint

# Test commands using uv
test: test-core test-api test-cli
	@echo "All tests completed successfully!"

test-core:
	@echo "Running Core package tests..."
	uv run --package shelly-manager-core pytest packages/core/tests/ -v

test-api:
	@echo "Running API package tests..."
	uv run --package shelly-manager-api pytest packages/api/tests/ -v

test-cli:
	@echo "Running CLI package tests..."
	uv run --package shelly-manager-cli pytest packages/cli/tests/ -v

test-web:
	@echo "Running Web package tests..."
	cd packages/web && npm test

test-coverage:
	@echo "Running all tests with coverage..."
	uv run pytest --cov=packages --cov-report=html --cov-report=term-missing

# Run commands
run-api:
	uv run --package shelly-manager-api python -m api.main

run-cli:
	uv run shelly-manager --help

# Development workflow
setup: clean install-dev
	@echo "Development environment setup complete with uv!"
	@echo "Run 'make run-cli' to test the CLI"
	@echo "Run 'make run-api' to start the API server"

# CI commands
ci-test: lint test-coverage
