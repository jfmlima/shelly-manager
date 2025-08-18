.PHONY: help install install-dev install-core install-api install-cli clean lint format test test-core test-api test-cli test-unit test-unit-core test-unit-api test-unit-cli test-integration test-coverage test-coverage-core test-coverage-api test-coverage-cli build build-core build-api build-cli run-api run-cli setup ci-test docker-build docker-run

# Default target
help:
	@echo "Shelly Manager - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  install       Install all packages in development mode"
	@echo "  install-dev   Install all packages with dev dependencies"
	@echo "  install-core  Install only core package"
	@echo "  install-api   Install core + api packages"
	@echo "  install-cli   Install core + cli packages"
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
	@echo "  test-unit     Run unit tests for all packages"
	@echo "  test-integration Run integration tests for all packages"
	@echo "  test-coverage Run all tests with coverage reports"
	@echo ""
	@echo "Build:"
	@echo "  build         Build all packages"
	@echo "  build-core    Build core package"
	@echo "  build-api     Build api package"
	@echo "  build-cli     Build cli package"
	@echo ""
	@echo "Run:"
	@echo "  run-api       Start the API server"
	@echo "  run-cli       Run CLI with sample scan"

# Installation commands
install:
	pip install -e packages/core
	pip install -e packages/api
	pip install -e packages/cli

install-dev: install
	pip install -e "packages/core[dev]"
	pip install -e "packages/api[dev]"
	pip install -e "packages/cli[dev]"
	pip install -e ".[dev]"

install-core:
	pip install -e packages/core

install-api: install-core
	pip install -e packages/api

install-cli: install-core
	pip install -e packages/cli

# Development commands
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml
	rm -rf packages/core/build/ packages/core/dist/ packages/core/htmlcov-core/ packages/core/.coverage
	rm -rf packages/api/build/ packages/api/dist/ packages/api/htmlcov-api/ packages/api/.coverage
	rm -rf packages/cli/build/ packages/cli/dist/ packages/cli/htmlcov-cli/ packages/cli/.coverage

format:
	black packages/
	ruff check --fix packages/

lint:
	black --check packages/
	ruff check packages/
	mypy packages/core/src/core
	mypy packages/api/src/api
	mypy packages/cli/src/cli

lint-web:
	@echo "Running web linting..."
	cd packages/web && npm run lint

# Test commands
test: test-core test-api test-cli
	@echo "All tests completed successfully!"

test-core:
	@echo "Running Core package tests..."
	cd packages/core && python -m pytest -v

test-api:
	@echo "Running API package tests..."
	cd packages/api && python -m pytest -v

test-cli:
	@echo "Running CLI package tests..."
	cd packages/cli && python -m pytest -v

test-unit: test-unit-core test-unit-api test-unit-cli
	@echo "All unit tests completed successfully!"

test-unit-core:
	@echo "Running Core unit tests..."
	cd packages/core && python -m pytest -v -m "unit" 2>/dev/null || python -m pytest -v

test-unit-api:
	@echo "Running API unit tests..."
	cd packages/api && python -m pytest -v -m "unit" 2>/dev/null || python -m pytest -v

test-unit-cli:
	@echo "Running CLI unit tests..."
	cd packages/cli && python -m pytest -v -m "unit" 2>/dev/null || python -m pytest -v

test-integration:
	@echo "Running integration tests..."
	cd packages/core && python -m pytest -v -m "integration" 2>/dev/null || echo "No integration tests in core"
	cd packages/api && python -m pytest -v -m "integration" 2>/dev/null || echo "No integration tests in api"
	cd packages/cli && python -m pytest -v -m "integration" 2>/dev/null || echo "No integration tests in cli"

test-coverage: test-coverage-core test-coverage-api test-coverage-cli
	@echo "All coverage reports generated!"

test-coverage-core:
	@echo "Running Core tests with coverage..."
	cd packages/core && python -m pytest --cov=core --cov-report=html:htmlcov-core --cov-report=term-missing

test-coverage-api:
	@echo "Running API tests with coverage..."
	cd packages/api && python -m pytest --cov=api --cov-report=html:htmlcov-api --cov-report=term-missing

test-coverage-cli:
	@echo "Running CLI tests with coverage..."
	cd packages/cli && python -m pytest --cov=cli --cov-report=html:htmlcov-cli --cov-report=term-missing

# Build commands
build: build-core build-api build-cli

build-core:
	cd packages/core && python -m build

build-api:
	cd packages/api && python -m build

build-cli:
	cd packages/cli && python -m build

# Run commands
run-api:
	cd packages/api && python -m api.main

run-cli:
	shelly-manager --help

# Development workflow
setup: clean install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make run-cli' to test the CLI"
	@echo "Run 'make run-api' to start the API server"

# CI commands
ci-test: lint test-coverage

# Docker commands (future)
docker-build:
	docker build -t shelly-manager:latest .

docker-run:
	docker run -p 8000:8000 shelly-manager:latest
