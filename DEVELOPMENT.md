# Development Setup and Testing

## Quick Start

1. **Install dependencies:**
   ```bash
   # Install core package first (required by CLI and API)
   cd packages/core
   pip install -e .

   # Install CLI package
   cd ../cli
   pip install -e .

   # Install API package (optional)
   cd ../api
   pip install -e .
   ```

2. **Test the core package:**
   ```bash
   cd packages/core
   python -c "from core.domain.entities.shelly_device import ShellyDevice; print('Core package working!')"
   ```

3. **Test CLI and API:**
   ```bash
   # CLI
   cd packages/cli && python -m cli --help

   # API
   cd packages/api && python -m api
   ```

## Development Installation

### Local Package Dependencies
Since the core package is not published to PyPI, install packages in this order:

```bash
# 1. Install core package first (required by CLI and API)
cd packages/core
pip install -e .

# 2. Install CLI package
cd ../cli
pip install -e .

# 3. Install API package (optional)
cd ../api
pip install -e .
```

### Virtual Environment Setup (Recommended)
```bash
# For CLI development
cd packages/cli
python -m venv venv
source venv/bin/activate
pip install -e ../core
pip install -e ".[dev]"

# For API development
cd packages/api
python -m venv venv
source venv/bin/activate
pip install -e ../core
pip install -e ".[dev]"
```

## Development Workflow

### Code formatting and linting
```bash
# Format code with black
black .

# Check with ruff
ruff check .

# Type checking
mypy .
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=app

# Run specific test types
pytest tests/unit/
pytest tests/integration/
```

### Running the Application
```bash
# Core functionality (verified working)
cd packages/core
python -c "from core.settings import settings; print(f'✅ Settings: {settings.api.host}:{settings.api.port}')"

# CLI usage (may require additional setup)
cd packages/cli
python -m cli scan 192.168.1.0/24
python -m cli status 192.168.1.100
python -m cli update 192.168.1.100

# API server (may require additional setup)
cd packages/api
python -m api.run_server
# Then visit http://localhost:8000/docs
```

> **Note**: CLI and API packages may need additional dependency resolution.
> All core business logic and domain functionality is working correctly.
