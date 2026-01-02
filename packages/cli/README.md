# Shelly Manager CLI

Command-line interface for managing Shelly devices locally. Built with Click.

## Features

- Network discovery to find Shelly devices
- Bulk operations across multiple devices
- Firmware update management
- Device configuration control
- Export results to JSON or CSV
- Rich terminal output with tables and progress bars
- Docker support

## Quick Start

### Docker

```bash
# Scan for devices
docker run --rm -it \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  scan --target 192.168.1.0/24

# Device status check
docker run --rm -it \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  device status 192.168.1.100

# Multi-target scan
docker run --rm -it \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  scan --target 192.168.1.10 --target 192.168.1.20-30
```

### Local Installation

```bash
# Install from project root
uv sync --package shelly-manager-cli --extra dev

# Run CLI commands
uv run shelly-manager --help
uv run shelly-manager scan --target 192.168.1.0/24
```

## Commands

### Global Options

```bash
shelly-manager [OPTIONS] COMMAND [ARGS]...

Options:
  --version            Show version and exit
  --help               Show help message
```

### Device Discovery

#### Scan Command

```bash
# Scan IP target
shelly-manager scan --target 192.168.1.0/24
shelly-manager scan --target 192.168.1.100-110

# Scan with multiple targets
shelly-manager scan --target 192.168.1.1 --target 10.0.0.0/24

# Scan with custom settings
shelly-manager scan --target 192.168.1.0/24 --timeout 5.0 --workers 25

# Export results
shelly-manager scan --target 192.168.1.0/24 --export json
shelly-manager scan --target 192.168.1.0/24 --export csv --export-file devices.csv
```

**Options:**

- `--target`: IP target (IP, range, or CIDR). Can be used multiple times.
- `--use-mdns`: Use mDNS service discovery
- `--timeout`: Timeout per device (default: 3.0s)
- `--workers`: Concurrent workers (default: 50)
- `--export`: Export format (json, csv)
- `--export-file`: Output file path

### Device Management

#### Device Commands

```bash
# Check device status
shelly-manager device status 192.168.1.100
shelly-manager device status 192.168.1.100 192.168.1.101

# Reboot devices
shelly-manager device reboot 192.168.1.100
shelly-manager device reboot 192.168.1.100 --force  # Skip confirmation
```

**Device Status Output:**

```
┌─────────────────┬──────────┬─────────────┬──────────────────┬─────────────┐
│ IP Address      │ Status   │ Device Type │ Device Name      │ Firmware    │
├─────────────────┼──────────┼─────────────┼──────────────────┼─────────────┤
│ 192.168.1.100   │ online   │ shelly1pm   │ Living Room      │ 20230913... │
│ 192.168.1.101   │ offline  │ unknown     │ -                │ -           │
└─────────────────┴──────────┴─────────────┴──────────────────┴─────────────┘
```

### Firmware Updates

#### Update Commands

```bash
# Check for available updates
shelly-manager update check --all
shelly-manager update check 192.168.1.100 192.168.1.101

# Apply firmware updates
shelly-manager update apply 192.168.1.100
shelly-manager update apply 192.168.1.100 --channel beta

# Check update status
shelly-manager update status 192.168.1.100
```

**Update Options:**

- `--channel`: Update channel (stable, beta) - default: stable
- `--force`: Skip confirmation prompts
- `--timeout`: Update timeout (default: 30s)

### Configuration Management

#### Config Commands

```bash
# Get device configuration
shelly-manager config get --ip 192.168.1.100
shelly-manager config get --ip 192.168.1.100 --output config.json

# Set device configuration
shelly-manager config set --ip 192.168.1.100 --config-file new-config.json
shelly-manager config set --ip 192.168.1.100 --key wifi.ssid --value "MyNetwork"
```

### Bulk Operations

#### Bulk Commands

```bash
# Bulk operations with device discovery
shelly-manager bulk reboot --target 192.168.1.0/24
shelly-manager bulk update --target 192.168.1.100-110

# Bulk operations on specific IPs
shelly-manager bulk reboot --target 192.168.1.100 --target 192.168.1.101
shelly-manager bulk update --target 192.168.1.100 --target 192.168.1.101 --channel beta
```

**Bulk Options:**

- `--target`: IP target (IP, range, or CIDR). Can be used multiple times.
- `--force`: Skip confirmation prompts
- `--workers`: Concurrent operations (default: 10)

## Configuration

### Environment Variables

| Variable             | Default       | Description                |
| -------------------- | ------------- | -------------------------- |
| `SHELLY_TIMEOUT`     | `3.0`         | Default timeout per device |
| `SHELLY_MAX_WORKERS` | `50`          | Default concurrent workers |


## Export Formats

### JSON Export

```bash
shelly-manager scan --target 192.168.1.0/24 --export json
```

**Output:**

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

### CSV Export

```bash
shelly-manager scan --target 192.168.1.0/24 --export csv --export-file devices.csv
```

**Output:**

```csv
ip,status,device_type,device_name,firmware_version,response_time,last_seen
192.168.1.100,online,shelly1pm,Living Room Light,20230913-112003,0.123,2024-01-15T10:30:00Z
192.168.1.101,offline,unknown,,,,
```

## Docker Usage

### Interactive Shell

```bash
# Run interactive CLI session
docker run --rm -it \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  bash

# Then run commands inside container
root@container:/app# shelly-manager scan --target 192.168.1.0/24
```

### Automated Scripts

```bash
#!/bin/bash
# Script to check device status daily

docker run --rm \
  -v ./reports:/app/reports \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  device status 192.168.1.0/24 --export json --export-file /app/reports/status-$(date +%Y%m%d).json
```

### Docker Compose

```yaml
services:
  cli:
    image: ghcr.io/jfmlima/shelly-manager-cli:latest
    volumes:
      - ./reports:/app/reports
    command: |
      sh -c '
        echo "Running daily device scan..."
        shelly-manager scan 192.168.1.0/24 --export csv --export-file /app/reports/devices.csv
      '
    profiles:
      - daily-scan
```

## Development

### Local Development Setup

```bash
# From project root
cd shelly-manager

# Install CLI package with dev dependencies
uv sync --package shelly-manager-cli --extra dev

# Run CLI directly
uv run shelly-manager --help

# Run tests
uv run --package shelly-manager-cli pytest packages/cli/tests/ -v

# Run linting
uv run ruff check packages/cli/
uv run mypy packages/cli/src/cli
```

### Adding New Commands

1. **Create Command Module**: Add to `packages/cli/src/cli/commands/`
2. **Add Use Cases**: Add business logic to `packages/cli/src/cli/use_cases/`
3. **Register Command**: Add to main CLI in `packages/cli/src/cli/main.py`
4. **Add Tests**: Create tests in `packages/cli/tests/`

Example command:

```python
import click
from cli.commands.common import async_command

@click.group()
def monitor():
    """Device monitoring commands."""
    pass

@monitor.command()
@click.option('--interval', default=60, help='Monitoring interval in seconds')
@async_command
async def watch(interval: int):
    """Watch device status continuously."""
    # Implementation here
    pass
```

### Testing

```bash
# Run all CLI tests
make test-cli

# Run specific test categories
uv run --package shelly-manager-cli pytest packages/cli/tests/unit/commands/ -v
uv run --package shelly-manager-cli pytest packages/cli/tests/unit/use_cases/ -v

# Test with coverage
uv run --package shelly-manager-cli pytest packages/cli/tests/ --cov=cli --cov-report=html
```

**Testing Documentation**: Tests are located in `packages/cli/tests/` with unit tests for commands and use cases.

## Architecture

The CLI follows Clean Architecture principles:

```
packages/cli/src/cli/
├── commands/             # Click command definitions
├── use_cases/           # CLI-specific business logic
├── entities/            # CLI data models
├── dependencies/        # Dependency injection
├── presentation/        # Output formatting and styles
└── main.py             # CLI entry point
```

### Key Components

- **Commands**: Click-based command definitions with argument parsing
- **Use Cases**: Business logic specific to CLI operations
- **Entities**: Data models for CLI operations (bulk requests, exports)
- **Presentation**: Rich formatting, tables, progress bars, and colors

### Dependencies

- **Click**: Command-line interface framework
- **Rich**: Rich text and beautiful formatting
- **Pydantic**: Data validation and serialization
- **Core Package**: Business logic and domain models

## Troubleshooting

### Common Issues

1. **Permission denied**: Ensure proper file permissions for config files
2. **Network timeout**: Increase timeout with `--timeout` option
3. **Too many workers**: Reduce workers with `--workers` option for slower networks
4. **Config file not found**: Check path and file permissions

### Debug Mode

Enable verbose output for debugging:

```bash
# Local installation
uv run shelly-manager --verbose scan 192.168.1.0/24

# Docker
docker run --rm -it \
  ghcr.io/jfmlima/shelly-manager-cli:latest \
  --verbose scan 192.168.1.0/24
```

### Performance Tuning

```bash
# For large networks, adjust workers and timeout
shelly-manager scan 192.168.0.0/16 --workers 100 --timeout 1.0

# For slow networks, reduce workers and increase timeout
shelly-manager scan 192.168.1.0/24 --workers 10 --timeout 10.0
```

## Additional Resources

- **Main Documentation**: [../../README.md](../../README.md)
- **Development Guide**: [../../DEVELOPMENT.md](../../DEVELOPMENT.md)
- **Core Package**: [../core/README.md](../core/README.md)
- **API Package**: [../api/README.md](../api/README.md)
- **Testing Guide**: [tests/README.md](tests/README.md)
