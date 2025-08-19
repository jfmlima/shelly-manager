# 🌐 Shelly Manager API

REST API server for Shelly Manager built with **Litestar** - a modern, high-performance async Python framework.

## ✨ Features

- **🚀 High Performance**: Async/await with Litestar framework
- **📖 OpenAPI Documentation**: Auto-generated interactive docs
- **🔒 Type Safety**: Request/response validation with Pydantic
- **🛡️ Error Handling**: Comprehensive error handling middleware
- **📊 Health Monitoring**: Built-in health checks and monitoring
- **🔧 CORS Support**: Configurable CORS for web UI integration
- **🐳 Docker Ready**: Production-ready Docker containers

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Run API server
docker run -p 8000:8000 \
  -v ./config.json:/app/config.json:ro \
  ghcr.io/jfmlima/shelly-manager/api:latest

# Visit API documentation
open http://localhost:8000/docs
```

### Local Development

```bash
# Install dependencies (from project root)
uv sync --package shelly-manager-api --extra dev

# Start development server
uv run --package shelly-manager-api python -m api.main

# API available at http://localhost:8000
# Docs available at http://localhost:8000/docs
```

## 🌐 API Endpoints

### Health & Status

```bash
GET /api/health                    # Service health check
```

### Device Discovery

```bash
GET /api/devices/scan              # Scan network for devices
  ?start_ip=192.168.1.1            # Start IP address
  &end_ip=192.168.1.254            # End IP address
  &use_predefined=true             # Use predefined ranges
  &timeout=3.0                     # Timeout per device
  &max_workers=50                  # Concurrent workers
```

### Device Operations

```bash
GET /api/devices/{ip}/status       # Get device status
  ?include_updates=true            # Include update information

POST /api/devices/{ip}/update      # Update device firmware
  ?channel=stable                  # Update channel (stable/beta)

POST /api/devices/{ip}/reboot      # Reboot device

POST /api/devices/bulk/update      # Bulk firmware updates
  # Body: {"device_ips": ["192.168.1.100", "192.168.1.101"], "channel": "stable"}
```

### Configuration Management

```bash
GET /api/devices/{ip}/config       # Get device configuration
POST /api/devices/{ip}/config      # Update device configuration
  # Body: {"config": {...}}

GET /api/config                    # Get global configuration
PUT /api/config                    # Update global configuration
```

### Monitoring (Future)

```bash
GET /api/actions                   # Get action history (coming soon)
GET /api/devices/updates           # Get update status (coming soon)
```

## 📋 Request/Response Examples

### Device Scan

```bash
curl "http://localhost:8000/api/devices/scan?start_ip=192.168.1.1&end_ip=192.168.1.10"
```

**Response:**

```json
[
  {
    "ip": "192.168.1.100",
    "status": "online",
    "device_type": "shelly1pm",
    "device_name": "Living Room Light",
    "firmware_version": "20230913-112003",
    "response_time": 0.123,
    "last_seen": "2024-01-15T10:30:00Z"
  }
]
```

### Device Update

```bash
curl -X POST "http://localhost:8000/api/devices/192.168.1.100/update?channel=stable"
```

**Response:**

```json
{
  "ip": "192.168.1.100",
  "success": true,
  "message": "Firmware update initiated",
  "action_type": "firmware_update"
}
```

### Error Response

```json
{
  "detail": "Device not reachable",
  "status_code": 404,
  "ip": "192.168.1.100"
}
```

## ⚙️ Configuration

### Environment Variables

| Variable             | Default       | Description                |
| -------------------- | ------------- | -------------------------- |
| `HOST`               | `127.0.0.1`   | API server host            |
| `PORT`               | `8000`        | API server port            |
| `DEBUG`              | `false`       | Enable debug mode          |
| `SHELLY_CONFIG_FILE` | `config.json` | Path to configuration file |

### Configuration File

Create a `config.json` file:

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

## 🐳 Docker Deployment

### Basic Deployment

```bash
docker run -d \
  --name shelly-manager-api \
  -p 8000:8000 \
  -v ./config.json:/app/config.json:ro \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  ghcr.io/jfmlima/shelly-manager/api:latest
```

### Docker Compose

```yaml
services:
  api:
    image: ghcr.io/jfmlima/shelly-manager/api:latest
    ports:
      - "8000:8000"
    volumes:
      - ./config.json:/app/config.json:ro
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=false
    restart: unless-stopped
```

### Health Check

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 🛠️ Development

### Local Development Setup

```bash
# From project root
cd shelly-manager

# Install with development dependencies
uv sync --package shelly-manager-api --extra dev

# Run with auto-reload
uv run --package shelly-manager-api python -m api.main

# Run tests
uv run --package shelly-manager-api pytest packages/api/tests/ -v

# Run linting
uv run ruff check packages/api/
uv run mypy packages/api/src/api
```

### API Documentation Development

The API uses Litestar's built-in OpenAPI generation:

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **OpenAPI Spec**: http://localhost:8000/schema/openapi.json

### Adding New Endpoints

1. **Create Controller**: Add to `packages/api/src/api/controllers/`
2. **Define DTOs**: Add request/response models to `packages/api/src/api/presentation/dto/`
3. **Add Route**: Register controller in `packages/api/src/api/main.py`
4. **Add Tests**: Create tests in `packages/api/tests/`

Example controller:

```python
from litestar import Controller, get
from api.presentation.dto.responses import DeviceResponse

class DeviceController(Controller):
    path = "/devices"

    @get("/{device_ip:str}/status")
    async def get_device_status(self, device_ip: str) -> DeviceResponse:
        # Implementation here
        pass
```

### Testing

```bash
# Run all API tests
make test-api

# Run specific test files
uv run --package shelly-manager-api pytest packages/api/tests/unit/controllers/ -v

# Run with coverage
uv run --package shelly-manager-api pytest packages/api/tests/ --cov=api --cov-report=html
```

## 🏗️ Architecture

The API follows Clean Architecture principles:

```
packages/api/src/api/
├── controllers/           # HTTP request handlers
├── dependencies/          # Dependency injection container
├── main.py               # Application entry point
└── presentation/
    ├── dto/              # Data Transfer Objects
    └── serializers/      # Response serialization
```

### Dependencies

- **Litestar**: Modern async web framework
- **Pydantic**: Data validation and serialization
- **uvicorn**: ASGI server
- **Core Package**: Business logic and domain models

## 🔧 Troubleshooting

### Common Issues

1. **Port already in use**: Change `PORT` environment variable
2. **Config file not found**: Ensure `config.json` exists and is mounted
3. **CORS errors**: Configure CORS settings for your web UI domain
4. **Health check failures**: Verify API is responding on configured port

### Debug Mode

Enable debug mode for detailed error messages:

```bash
docker run -p 8000:8000 \
  -e DEBUG=true \
  ghcr.io/jfmlima/shelly-manager/api:latest
```

### Logs

```bash
# View container logs
docker logs shelly-manager-api

# Follow logs in real-time
docker logs -f shelly-manager-api
```

## 📚 Additional Resources

- **Main Documentation**: [../../README.md](../../README.md)
- **Development Guide**: [../../DEVELOPMENT.md](../../DEVELOPMENT.md)
- **Core Package**: [../core/README.md](../core/README.md)
- **CLI Package**: [../cli/README.md](../cli/README.md)

---

**🌐 Built with Litestar for high-performance async API serving**
