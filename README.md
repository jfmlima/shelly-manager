# 🏠 Shelly Manager - Smart Device Management Platform

A production-ready monorepo for managing Shelly IoT devices featuring device discovery, firmware updates, configuration management, and monitoring capabilities.

## 🏗️ Project Architecture

```
shelly-manager/
├── packages/
│   ├── core/              # 🏛️ Business Logic & Domain Models
│   ├── api/               # 🌐 HTTP REST API (Litestar)
│   └── cli/               # 💻 Command Line Interface (Click)
├── config.json            # Device configuration
├── Makefile              # Development commands
└── pyproject.toml        # Workspace configuration
```

### 📦 Package Overview

- **🏛️ Core** - Pure business logic, domain models, and use cases
- **🌐 API** - HTTP REST API for web applications and integrations
- **💻 CLI** - Modern command-line interface with rich output

## 🚀 Quick Start

### Installation

```bash
# Install core package first (required by both CLI and API)
cd packages/core
pip install -e .

# Install CLI package
cd ../cli
pip install -e .

# Install API package (optional)
cd ../api
pip install -e .
```

### Alternative: Development Setup with Virtual Environment

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

### CLI Usage

```bash
# Scan for devices
shelly-manager scan --range 192.168.1.0/24

# List devices from configuration
shelly-manager device list --from-config

# Check device status
shelly-manager device status 192.168.1.100

# Update firmware
shelly-manager update check --all

# Bulk operations
shelly-manager bulk reboot --scan
```

### API Usage

```bash
# Start the API server
cd packages/api
python -m api

# API will be available at http://localhost:8000
curl http://localhost:8000/health
```


## 💻 CLI Commands

### Device Management
```bash
# Scan for devices
shelly-manager scan --range 192.168.1.0/24
shelly-manager device scan --from-config

# List devices with details
shelly-manager device list --from-config

# Check device status
shelly-manager device status 192.168.1.100 192.168.1.101
shelly-manager device status --from-config

# Reboot devices
shelly-manager device reboot 192.168.1.100 --force
```

### Firmware Updates
```bash
# Check for updates
shelly-manager update check --all

# Update specific devices
shelly-manager update apply 192.168.1.100

# Check update status
shelly-manager update status
```

### Bulk Operations
```bash
# Bulk reboot with device discovery
shelly-manager bulk reboot --scan

# Bulk operations on configured devices
shelly-manager bulk update --from-config
```

### Configuration Management
```bash
# Get device configuration
shelly-manager config get --ip 192.168.1.100

# Set device configuration
shelly-manager config set --ip 192.168.1.100 --key wifi.ssid --value "MyNetwork"

# Manage predefined IPs
shelly-manager config ips add 192.168.1.100
shelly-manager config ips list
```

## 🌐 API Endpoints

When running the API server (`cd packages/api && python -m api`):

```bash
# Health check
GET /health

# Device operations
GET /api/devices/scan
GET /api/devices/{ip}/status
POST /api/devices/{ip}/update
POST /api/devices/{ip}/reboot

# Configuration
GET /api/config
PUT /api/config
GET /api/config/predefined-ips
PUT /api/config/predefined-ips

# Monitoring
GET /api/actions
GET /api/devices/updates
```

## 🛠️ Development

### Available Commands
```bash
make help           # Show all available commands
make install        # Install all packages
make install-dev    # Install with dev dependencies
make clean         # Clean build artifacts
make lint          # Run linting
make test          # Run tests
make run-cli       # Test CLI
make run-api       # Start API server
```

### Pre-commit Hooks
Pre-commit hooks are configured to run linting and tests automatically before each commit:

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Run hooks on specific files
pre-commit run --files path/to/file.py
```

The hooks will automatically:
- Run `make lint` (black, ruff, mypy)
- Run `make test` (all package tests)
- Fix trailing whitespace and file endings
- Check YAML, TOML, and JSON syntax

### Package Development
```bash
# Install specific packages
make install-core   # Core business logic only
make install-api    # Core + API
make install-cli    # Core + CLI
```

## ✨ Features

### 🔍 **Device Discovery**
- Network scanning with IP ranges and CIDR notation
- Configuration-based device lists
- Async scanning with configurable workers

### 🔄 **Firmware Management**
- Automatic update checking
- Safe firmware updates
- Update status monitoring

### ⚙️ **Configuration Management**
- Get/set device configurations
- JSON configuration support
- Bulk configuration operations

### 📊 **Rich Output**
- Beautiful table formatting
- Progress indicators
- Colored status messages
- Export to JSON/CSV

### 🏗️ **Architecture**
- Clean Architecture principles
- Domain-Driven Design
- Async/await support
- Type safety with Pydantic

## 📋 Requirements

- **Python 3.11+**
- **Network access** to Shelly devices
- **Optional**: Device credentials for authenticated devices

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes following the architecture principles
4. **Add** tests for new functionality
5. **Submit** a pull request

### Development Guidelines

- Follow **Clean Architecture** principles
- Keep **domain logic** in the core package
- Use **dependency injection** for external dependencies
- Write **comprehensive tests**
- Maintain **type safety** with type hints

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
---

**Made with ❤️ for the smart home community**
