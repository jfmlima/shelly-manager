# Shelly Manager CLI

Command-line interface for managing Shelly devices locally. Built with Click.

## Features

- Network discovery to find Shelly devices
- Bulk operations across multiple devices
- Firmware update management
- Device configuration control
- Configuration backup & restore (encrypted snapshots)
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

### Credential Management

Manage credentials for password-protected Shelly Gen2 devices.

**Note:** Requires `SHELLY_SECRET_KEY` environment variable for encryption.

```bash
# Set credentials for a specific device (by MAC address)
shelly-manager credentials set AABBCCDDEEFF mypassword
shelly-manager credentials set AABBCCDDEEFF mypassword --username admin

# Set global fallback credentials (used when device-specific not found)
shelly-manager credentials set-global myfallbackpassword

# List all stored credentials (passwords hidden)
shelly-manager credentials list

# Delete credentials for a device
shelly-manager credentials delete AABBCCDDEEFF
```

**Credentials Options:**

- `--username`: Device username (default: admin)

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

### Configuration Backup & Restore

Capture a per-device configuration snapshot and restore it later. Backups are stored
server-side in the local database (encrypted with `SHELLY_SECRET_KEY`) and keyed by device
MAC. They are not written to files.

```bash
# Capture a backup of a device
shelly-manager backup create --target 192.168.1.100 --name before-upgrade

# List stored backups (optionally filter by MAC)
shelly-manager backup list
shelly-manager backup list --mac AABBCCDDEEFF

# Restore a backup onto a device (by backup id)
shelly-manager backup restore 1 --target 192.168.1.100

# Restore only selected components
shelly-manager backup restore 1 --target 192.168.1.100 --component switch:0 --component sys

# Delete a backup
shelly-manager backup delete 1
```

**Restore Options:**

- `--target` / `-t`: Target device IP (required).
- `--component`: Component key to restore (repeatable). Omit to restore all components except
  network types; pass keys to choose a subset.
- `--all`: Include network components (`wifi`/`eth`/`mqtt`/`ws`/`cloud`), which are excluded by
  default to avoid losing connectivity.
- `--allow-mac-mismatch`: Restore even if the target MAC differs from the backup.
- `--reboot`: Reboot the device after a successful restore.
- `--force`: Skip the confirmation prompt.

> **Backup/restore vs. `bulk config`:** use backup/restore to recover a single device from its
> own snapshot. Use `bulk config apply` to push the same settings out to many devices at once.
> Restore works on Gen2+ devices only.

### Scheduled Backups

Run backups automatically on a schedule and prune old snapshots with a retention policy. The
schedules are stored in the same local database and executed by the API server's in-process
scheduler, so the API needs to be running for them to fire. The CLI manages the schedules.

```bash
# Create a daily schedule for two devices, keeping the 7 newest snapshots per device
shelly-manager backup schedule create --name nightly \
  --every daily --target 192.168.1.100 --target 192.168.1.101 --keep-last 7

# Use a custom cadence and target every device with stored credentials
shelly-manager backup schedule create --name fleet \
  --interval-seconds 21600 --all-credentialed --max-age-days 30

# List, enable, disable, run now, and delete
shelly-manager backup schedule list
shelly-manager backup schedule disable 1
shelly-manager backup schedule enable 1
shelly-manager backup schedule run 1
shelly-manager backup schedule delete 1 --force
```

**Create options:**

- `--name`: Unique schedule name (required).
- `--every`: Preset cadence (`hourly`, `daily`, `weekly`). Provide this or `--interval-seconds`,
  not both.
- `--interval-seconds`: Custom cadence in seconds (minimum 60).
- `--target` / `-t`: Target device IP, range, or CIDR (repeatable). Ranges and CIDR are scanned
  for live Shelly devices at run time, so only discovered devices are backed up.
- `--mac`: Target device MAC (repeatable). Resolved to an IP through the device's last-seen
  address; a MAC with no known IP is reported as skipped, not failed.
- `--all-credentialed`: Back up every device that has stored credentials.
- `--keep-last`: Keep only the newest N scheduled backups per device.
- `--max-age-days`: Drop scheduled backups older than N days.
- `--disabled`: Create the schedule without enabling it.

Retention only ever removes scheduled snapshots, so a manual backup you captured by hand is never
deleted by a schedule. A missed run (the device or API was down) fires once on catch-up rather
than backfilling every slot it missed. The first run happens one interval after creation; use
`backup schedule run` if you want a snapshot right away.

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
