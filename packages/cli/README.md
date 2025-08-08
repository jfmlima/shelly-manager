# Shelly Manager CLI

Command-line interface for Shelly Manager.

## Installation

Install core package first as dependency, then install CLI package.

## Development Setup

Set up development environment with core package dependency.

## Usage

Scan for devices using network discovery:
- IP range scanning
- Configuration-based device lists

Check device status and health:
- Individual device status
- Bulk status checking

Update device firmware:
- Check for available updates
- Apply firmware updates

Control device operations:
- Reboot devices
- Configuration management

Access device configuration:
- Retrieve current configuration
- Update device settings

## Command Structure

The CLI is organized into logical command groups for different operations, with support for both individual device operations and bulk actions.
```

Set configuration:
```bash
shelly-manager set-config --ip 192.168.1.100 --config-file config.json
```

Bulk operations:
```bash
shelly-manager bulk --action update --ips 192.168.1.100,192.168.1.101
```

## Configuration

Create a configuration file:
```bash
shelly-manager --create-config
```

Use configuration file:
```bash
shelly-manager scan --config shelly_config.json
```

## Export Results

Export scan results to JSON or CSV:
```bash
shelly-manager scan --start 192.168.1.100 --end 110 --export json
shelly-manager scan --config config.json --export csv --export-file results.csv
```

## Development

See the main project README for development setup instructions.
