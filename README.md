# Shelly Manager

Local management for Shelly IoT devices without cloud connectivity.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/jfmlima/shelly-manager.svg)](https://github.com/jfmlima/shelly-manager/releases)
[![API Pulls](https://img.shields.io/docker/pulls/ghcr.io/jfmlima/shelly-manager-api)](https://github.com/jfmlima/shelly-manager/pkgs/container/shelly-manager-api)
[![CLI Pulls](https://img.shields.io/docker/pulls/ghcr.io/jfmlima/shelly-manager-cli)](https://github.com/jfmlima/shelly-manager/pkgs/container/shelly-manager-cli)
[![Web Pulls](https://img.shields.io/docker/pulls/ghcr.io/jfmlima/shelly-manager-web)](https://github.com/jfmlima/shelly-manager/pkgs/container/shelly-manager-web)

Manage Shelly devices on your local network without connecting them to the Shelly Cloud. Scan for devices, update firmware, manage configurations, and monitor status - all locally.

## Features

- Device discovery by network scanning
- Firmware update management (stable/beta channels)
- Device configuration changes
- Bulk operations across multiple devices
- Status monitoring
- Component action discovery and execution
- Dynamic device capability detection
- Component-specific controls (switches, covers, lights, etc.)

Available as:

- Web interface
- Command line tool
- REST API

## Quick Start

### Docker

**Web UI + API Stack**:

```yaml
services:
  shelly-manager-api:
    image: ghcr.io/jfmlima/shelly-manager-api:latest
    ports:
      - "8000:8000"
    volumes:
      - ./config.json:/app/config.json:ro
    environment:
      - HOST=0.0.0.0
      - PORT=8000

  shelly-manager-web:
    image: ghcr.io/jfmlima/shelly-manager-web:latest
    ports:
      - "8080:8080"
    environment:
      - VITE_BASE_API_URL=http://localhost:8000
    depends_on:
      - api
```

**With Traefik**:

```yaml
services:
  shelly-manager-api:
    container_name: shelly-manager-api
    image: ghcr.io/jfmlima/shelly-manager-api:latest
    volumes:
      - ./home/shelly-manager/config.json:/app/config.json:ro
    environment:
      - HOST=0.0.0.0
      - PORT=8000
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.shelly-manager-api.rule=Host(`shelly-manager-api.your.domain`)"
      - "traefik.http.routers.shelly-manager-api.service=shelly-manager-api"
      - "traefik.http.routers.shelly-manager-api.entrypoints=web"
      - "traefik.http.services.shelly-manager-api.loadbalancer.server.port=8000"

  shelly-manager-web:
    container_name: shelly-manager-web
    image: ghcr.io/jfmlima/shelly-manager-web:latest
    environment:
      - VITE_BASE_API_URL=http://shelly-manager-api.your.domain
    depends_on:
      - shelly-manager-api
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.shelly-manager-web.rule=Host(`shelly-manager.your.domain`)"
      - "traefik.http.routers.shelly-manager-web.service=shelly-manager-web"
      - "traefik.http.routers.shelly-manager-web.entrypoints=web"
      - "traefik.http.services.shelly-manager-web.loadbalancer.server.port=8080"
```

**CLI Only**:

```bash
# Interactive device scanning
docker run --rm -it \
  -v ./config.json:/app/config.json:ro \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  scan --range 192.168.1.0/24

# Check device status
docker run --rm -it \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  device status 192.168.1.100

# Bulk firmware updates
docker run --rm -it \
  -v ./config.json:/app/config.json:ro \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  bulk update --from-config
```

**API Only**:

```bash
docker run -p 8000:8000 \
  -v ./config.json:/app/config.json:ro \
  ghcr.io/jfmlima/shelly-manager-api:latest
```

### 📋 Configuration

Create a `config.json` file for device management:

```json
{
  "device_ips": ["192.168.1.100", "192.168.1.101"],
  "predefined_ranges": [
    {
      "start": "192.168.1.1",
      "end": "192.168.1.254"
    }
  ],
  "timeout": 3.0,
  "max_workers": 50
}
```

## 🏗️ Architecture

Shelly Manager follows Clean Architecture principles with a modular, package-based design:

```
shelly-manager/
├── packages/
│   ├── core/              # 🏛️ Business Logic & Domain Models
│   ├── api/               # 🌐 HTTP REST API (Litestar)
│   ├── cli/               # 💻 Command Line Interface (Click)
│   └── web/               # 🖥️ Modern Web UI (React + TypeScript)
├── config.json            # Device configuration
└── docker-compose.yml     # Development environment
```

### 📦 Package Overview

| Package                       | Purpose                                             | Documentation                          |
| ----------------------------- | --------------------------------------------------- | -------------------------------------- |
| **🏛️ [Core](packages/core/)** | Pure business logic, domain models, and use cases   | [Core README](packages/core/README.md) |
| **🌐 [API](packages/api/)**   | HTTP REST API for web applications and integrations | [API README](packages/api/README.md)   |
| **💻 [CLI](packages/cli/)**   | Modern command-line interface with rich output      | [CLI README](packages/cli/README.md)   |
| **🖥️ [Web](packages/web/)**   | Responsive web UI for device management             | [Web README](packages/web/README.md)   |

## 🌐 API Overview

The REST API provides complete device management capabilities:

```bash
# Health and status
GET /api/health                    # Service health check
GET /api/devices/scan              # Discover devices on network
GET /api/devices/{ip}/status       # Get device status

# Device operations
POST /api/devices/{ip}/update      # Update device firmware
POST /api/devices/{ip}/reboot      # Reboot device
POST /api/devices/bulk/update      # Bulk firmware updates

# Component Actions
GET /api/devices/{ip}/components/actions           # Discover available actions
POST /api/devices/{ip}/components/{id}/action      # Execute component action

# Configuration management
GET /api/devices/{ip}/config       # Get device configuration
POST /api/devices/{ip}/config      # Update device configuration
```

**API Documentation**: Start the API server and visit `http://localhost:8000/docs` for interactive OpenAPI documentation.

## 💻 CLI Overview

The CLI provides powerful automation capabilities:

```bash
# Device discovery
shelly-manager scan --range 192.168.1.0/24
shelly-manager device list --from-config

# Device operations
shelly-manager device status 192.168.1.100
shelly-manager device reboot 192.168.1.100
shelly-manager update check --all

# Bulk operations
shelly-manager bulk reboot --scan
shelly-manager bulk update --from-config
```

**CLI Documentation**: See [CLI README](packages/cli/README.md) for complete command reference.

## 🖥️ Web UI Overview

The web interface provides an intuitive management experience:

- **Device Discovery**: Network scanning with visual results
- **Bulk Operations**: Select multiple devices for batch operations
- **Real-time Status**: Live device status monitoring
- **Configuration Management**: Easy device configuration editing
- **Dark Mode**: System-aware theme switching

**Web Documentation**: See [Web README](packages/web/README.md) for setup and features.

## 📋 Requirements

- **Docker** (recommended) or **Python 3.11+**
- **Network access** to Shelly devices on your local network
- **Optional**: Device credentials for authenticated devices

## 🛠️ Development

For local development and contributing to Shelly Manager:

```bash
# Clone and setup development environment
git clone https://github.com/jfmlima/shelly-manager.git
cd shelly-manager

# Start development stack
docker-compose up -d

# Or install locally with uv
uv sync --extra dev
```

**Development Guide**: See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions, testing, and contribution guidelines.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
4. **Make** your changes following our [development guidelines](DEVELOPMENT.md)
5. **Add** tests for new functionality
6. **Submit** a pull request

### Development Principles

- **Clean Architecture**: Keep domain logic in the core package
- **Type Safety**: Use comprehensive type hints throughout
- **Testing**: Write tests for all new functionality
- **Documentation**: Update relevant documentation for changes

### Getting Help

- 📖 **Documentation**: Check package-specific READMEs
- 🐛 **Bug Reports**: Open an issue with reproduction steps
- 💡 **Feature Requests**: Describe your use case in an issue
- 💬 **Questions**: Start a discussion for general questions

## License

MIT License - see [LICENSE](LICENSE) file.
