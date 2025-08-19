# Development Setup and Testing

## Quick Start

1. **Install uv:**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or
   pip install uv
   ```

2. **Install dependencies:**

   ```bash
   # Install all workspace packages with dev dependencies
   uv sync --extra dev
   ```

3. **Test packages:**

   ```bash
   # Test everything
   make test

   # Test specific packages
   make test-core
   make test-api
   make test-cli
   ```

## Development Installation

### Workspace Setup

The project uses uv workspace dependencies for consistent version management:

```bash
# Install everything
uv sync --extra dev

# Install without dev dependencies
uv sync --no-dev

# Install specific package
uv sync --package shelly-manager-core
```

### Running Applications

```bash
# CLI
uv run shelly-manager --help

# API server
uv run --package shelly-manager-api python -m api.main
```

## Development Workflow

### Code formatting and linting

```bash
# Format code
make format

# Check linting
make lint
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific package tests
uv run --package shelly-manager-core pytest packages/core/tests/
```

### Running the Application

```bash
# Core functionality
uv run --package shelly-manager-core python -c "from core.domain.entities.shelly_device import ShellyDevice; print('✅ Core package working!')"

# CLI usage
uv run shelly-manager scan --help
uv run shelly-manager device status --help

# API server
uv run --package shelly-manager-api python -m api.main
# Then visit http://localhost:8000/docs
```
