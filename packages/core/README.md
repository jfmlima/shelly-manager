# 🏛️ Shelly Manager Core

The foundational business logic package for Shelly Manager

## ✨ What is Core?

The Core package contains the **pure business logic** that defines how Shelly Manager works. It's framework-agnostic and can be used by any interface (CLI, API, Web, etc.).

### 🎯 Purpose

- **Domain Models**: Define what a Shelly device is and how it behaves
- **Business Rules**: Implement the rules for device operations
- **Use Cases**: Orchestrate business operations (scan, update, reboot)
- **Gateways**: Define contracts for external dependencies
- **Independence**: No dependencies on frameworks, databases, or UI

## 🏗️ Architecture

This package follows **Clean Architecture** principles with clear separation of concerns:

```
packages/core/src/core/
├── domain/                    # 🏛️ Core business logic (innermost layer)
│   ├── entities/             # Business objects (ShellyDevice)
│   ├── value_objects/        # Immutable data objects
│   ├── services/             # Domain business logic
│   └── enums/               # Domain enumerations
├── use_cases/                # 🔄 Application business logic
│   ├── scan_devices.py      # Device discovery use case
│   ├── update_device_firmware.py
│   ├── reboot_device.py
│   └── ...
├── gateways/                 # 🌐 External interfaces (abstract)
│   ├── device/              # Device communication contracts
│   ├── configuration/       # Configuration management contracts
│   └── network/             # Network communication contracts
└── settings.py              # Configuration and shared utilities
```

### 🔄 Dependency Flow

```
External Interfaces → Use Cases → Domain Services → Entities
     (CLI/API)         ↑              ↑              ↑
                   Gateways      Value Objects    Enums
```

**Key Principle**: Dependencies point **inward**. The domain knows nothing about external concerns.

## 🚀 Quick Start

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
    start_ip="192.168.1.1",
    end_ip="192.168.1.10"
)

print(f"Scanning {scan_request.get_ip_count()} IP addresses")
```

## 📚 Additional Resources

- **Main Documentation**: [../../README.md](../../README.md)
- **Development Guide**: [../../DEVELOPMENT.md](../../DEVELOPMENT.md)
- **API Package**: [../api/README.md](../api/README.md) (implements Core interfaces)
- **CLI Package**: [../cli/README.md](../cli/README.md) (uses Core use cases)

---

**🏛️ Built with Clean Architecture for maximum flexibility and testability**
