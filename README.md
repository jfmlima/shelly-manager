# Shelly Device Manager

A production-ready Shelly Gen4 device scanner and management tool that supports discovery, firmware updates, configuration, and monitoring with **action-based operations**.

## Project Structure

The project has been organized into multiple modules for better maintainability:

```
src/
├── __init__.py          # Package initialization
├── main.py             # Main entry point
├── cli.py              # Command-line interface with action support
├── models.py           # Data models (DeviceStatus, ShellyDevice)
├── scanner.py          # Core scanning functionality
├── network.py          # Network utilities and RPC client
├── exporter.py         # Export functionality (JSON, CSV)
├── ui.py               # Display utilities and progress handling
├── actions.py          # Action definitions (list, update, reboot, etc.)
└── config.py           # Configuration constants and settings
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The tool now supports **discrete actions** that can be performed on discovered devices:

### Available Actions

- **`list`** - Discover and list Shelly devices (no modifications)
- **`update`** - Check for and apply firmware updates
- **`reboot`** - Reboot Shelly devices
- **`status`** - Get detailed device status, system information, and available updates
- **`config-get`** - Get device configuration
- **`config-set`** - Set device configuration

### Basic Examples

```bash
# List/discover devices without any modifications
python -m src.main --start 192.168.1.100 --end 150 --action list

# Update firmware on devices in range
python -m src.main --start 192.168.1.1 --end 254 --action update --verbose

# Reboot specific devices
python -m src.main --start 192.168.1.100 --end 105 --action reboot --username admin --password secret

# Get detailed device status with update information
python -m src.main --start 192.168.1.1 --end 50 --action status --export json

# Get device configurations
python -m src.main --start 192.168.1.1 --end 10 --action config-get --export json
```

### Advanced Configuration Management

```bash
# Set configuration from JSON file
python -m src.main --start 192.168.1.100 --end 105 --action config-set --config-file config.json

# Set configuration from JSON string
python -m src.main --start 192.168.1.100 --end 105 --action config-set --config-data '{"wifi":{"enable":true}}'
```

### Performance Tuning

```bash
# High-performance scanning
python -m src.main --start 192.168.1.1 --end 50 --action list --max-workers 100 --timeout 5
```

## Features

- **Action-Based Operations**: Choose specific actions to perform (list, update, reboot, config, status)
- **Device Discovery**: Automatically detect Shelly Gen4 devices on the network
- **Firmware Updates**: Check for and initiate firmware updates
- **Configuration Management**: Get and set device configurations with JSON support
- **Device Control**: Reboot devices remotely
- **Status Monitoring**: Get detailed device status and system information
- **Authentication Support**: Handle devices with authentication
- **Export Results**: Export action results to JSON or CSV with detailed information
- **Multi-threading**: Concurrent operations for improved performance
- **Progress Tracking**: Real-time progress updates during operations
- **Comprehensive Logging**: Detailed logging with verbose mode

## Architecture Benefits

### Decoupled Actions
Actions are now completely decoupled from the scanning logic:
- **Single Responsibility**: Each action has one clear purpose
- **Extensibility**: Easy to add new actions without modifying existing code
- **Reusability**: Actions can be used independently or combined
- **Testability**: Each action can be unit tested in isolation

### Flexible Operations
- **Selective Operations**: Only perform the actions you need
- **Non-destructive Discovery**: List devices without making any changes
- **Targeted Updates**: Update only when needed, reboot only when required
- **Configuration Management**: Separate get/set operations for better control

## Module Overview

### Models (`models.py`)
- `DeviceStatus`: Enumeration of possible device states
- `ShellyDevice`: Data class representing a Shelly device with all its properties

### Network (`network.py`)
- `NetworkUtils`: IP range generation and network utilities
- `ShellyRPCClient`: RPC communication with Shelly devices

### Scanner (`scanner.py`)
- `DeviceManager`: Executes actions on individual devices
- `ShellyScanner`: Main scanner class with action-based range operations

### Actions (`actions.py`)
- `DeviceAction`: Abstract base class for all actions
- `ListAction`: Discover devices without modifications
- `UpdateAction`: Check for and apply firmware updates
- `RebootAction`: Reboot devices
- `ConfigAction`: Get or set device configuration
- `StatusAction`: Get detailed device status
- `AVAILABLE_ACTIONS`: Registry of all available actions

### Export (`exporter.py`)
- `ResultsExporter`: Export action results to various formats

### UI (`ui.py`)
- `DisplayUtils`: Progress callbacks and result summary display with action context

### CLI (`cli.py`)
- `CLI`: Command-line interface with action selection and validation

## API Usage

You can also use the modules programmatically with the new action-based approach:

```python
from src import ShellyScanner, DisplayUtils, AVAILABLE_ACTIONS

# Create scanner
with ShellyScanner(timeout=5, max_workers=100, verbose=True) as scanner:
    # Execute specific action on range
    results = scanner.execute_action_range(
        "192.168.1.1", 50, "list",
        progress_callback=DisplayUtils.action_progress_callback
    )
    
    # Extract devices and action results
    devices = [device for device, _ in results]
    action_results = [result for _, result in results]
    
    # Print action-specific summary
    DisplayUtils.print_action_summary(devices, action_results, "list")
    
    # Execute different action on specific device
    device, result = scanner.device_manager.execute_action(
        "192.168.1.100", AVAILABLE_ACTIONS["status"]
    )
```

## Key Improvements from Refactoring

### 🎯 **Decoupled Actions**
- **Before**: Scanning always included update checking and was tightly coupled
- **After**: Choose exactly what action to perform (list, update, reboot, config, status)
- **Benefit**: No unintended side effects, clear operation intent

### 🧩 **Modular Architecture**
- **Before**: Single 500+ line monolithic file
- **After**: 10 focused modules with single responsibilities
- **Benefit**: Easy to maintain, extend, and test individual components

### 🔧 **Flexible Configuration**
- **Before**: Limited configuration options
- **After**: JSON-based configuration with file or string input
- **Benefit**: Complex configurations, scripting support, version control

### 📊 **Rich Export Options**
- **Before**: Basic device information export
- **After**: Action results, detailed status, configuration data
- **Benefit**: Better reporting, analysis, and audit trails

### 🚀 **Enhanced Performance**
- **Before**: Fixed operation pattern
- **After**: Optimized per-action execution with targeted RPC calls
- **Benefit**: Faster operations, reduced network overhead

## Migration Guide

### From Old CLI
```bash
# Old: Auto-update during scan
python main.py --start 192.168.1.100 --end 150

# New: Explicit action-based approach
python -m src.main --start 192.168.1.100 --end 150 --action list        # Just discover
python -m src.main --start 192.168.1.100 --end 150 --action update      # Discover + update
```

### From Old API
```python
# Old: Tightly coupled
scanner.scan_range(start, end)  # Always did discovery + update check

# New: Action-based
scanner.execute_action_range(start, end, "list")      # Just discovery
scanner.execute_action_range(start, end, "update")    # Discovery + update
scanner.execute_action_range(start, end, "reboot")    # Discovery + reboot
```
