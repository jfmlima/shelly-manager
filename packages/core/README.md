# Shelly Manager Core

The business logic package for Shelly Manager.

## What is Core?

Contains the core business logic that defines how Shelly Manager works. Framework-agnostic and can be used by any interface (CLI, API, Web).

### Purpose

- Domain models for Shelly devices and operations
- Business rules for device management
- Use cases that orchestrate operations (scan, update, reboot)
- Component action discovery and execution use cases
- Gateway contracts for external dependencies
- No dependencies on frameworks, databases, or UI

## Architecture

Follows Clean Architecture principles:

```
packages/core/src/core/
├── domain/                    # Core business logic
│   ├── entities/             # Business objects (ShellyDevice)
│   ├── value_objects/        # Immutable data objects
│   ├── services/             # Domain business logic
│   └── enums/               # Domain enumerations
├── use_cases/                # Application business logic
│   ├── scan_devices.py      # Device discovery
│   ├── update_device_firmware.py
│   ├── reboot_device.py
│   ├── execute_component_action.py    # Component action execution
│   ├── get_component_actions.py       # Component action discovery
│   └── ...
├── gateways/                 # External interfaces (abstract)
│   ├── device/              # Device communication contracts
│   └── network/             # Network communication contracts
└── settings.py              # Configuration and utilities
```

Dependencies point inward - the domain layer knows nothing about external concerns.

## Quick Start

### Installation

```bash
# Install core package only
uv sync --package shelly-manager-core

# Or install with dev dependencies
uv sync --package shelly-manager-core --extra dev
```

### Basic Usage

```python
import asyncio
from core.domain.entities.shelly_device import ShellyDevice
from core.domain.value_objects.scan_request import ScanRequest

# Create a Shelly device
device = ShellyDevice(
    ip="192.168.1.100",
    device_type="shelly1pm",
    device_name="Living Room Light"
)

print(f"Device: {device.device_name} at {device.ip}")
print(f"Status: {'Online' if device.is_online() else 'Offline'}")

# Create a scan request
scan_request = ScanRequest(
    targets=["192.168.1.1-10", "10.0.0.0/24"],
    timeout=3.0
)

print(f"Scanning with {len(scan_request.targets)} targets")
```

## Additional Resources

- **Main Documentation**: [../../README.md](../../README.md)
- **Development Guide**: [../../DEVELOPMENT.md](../../DEVELOPMENT.md)
- **API Package**: [../api/README.md](../api/README.md) (implements Core interfaces)
- **CLI Package**: [../cli/README.md](../cli/README.md) (uses Core use cases)
