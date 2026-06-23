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
│   ├── backup_device_config.py        # Capture & persist a config snapshot
│   ├── restore_device_config.py       # Restore a snapshot to a device
│   ├── manage_backup_schedules.py     # CRUD + enable/disable for schedules
│   ├── run_due_backups.py             # Run due schedules with retention
│   └── ...
├── gateways/                 # External interfaces (abstract)
│   ├── device/              # Device communication contracts
│   └── network/             # Network communication contracts
└── settings.py              # Configuration and utilities
```

Dependencies point inward - the domain layer knows nothing about external concerns.

## Authentication Services

The core package provides authentication services for password-protected Shelly Gen2 devices:

- **AuthenticationService** - Resolves credentials for devices (device-specific → global fallback)
- **AuthStateCache** - Tracks which devices require authentication with TTL-based expiration
- **EncryptionService** - Fernet symmetric encryption for stored passwords

These services enable the API and CLI to work with password-protected devices using HTTP Digest Auth.

## Backup & Restore Services

The core package provides per-device configuration backup and restore:

- **BackupDeviceConfig** - Captures a full per-component snapshot of one device (config plus
  script code and schedules) and persists it via `BackupRepository`. The snapshot is encrypted
  at rest with `EncryptionService` and keyed by device MAC.
- **RestoreDeviceConfig** - Applies a stored snapshot back to a device, per component key. The
  target MAC is validated against the backup; network components (`wifi`/`eth`/`mqtt`/`ws`/
  `cloud`) are excluded by default to avoid lockout; read-only fields are stripped before each
  `SetConfig`. Restore is supported on Gen2+ devices only.

Backups are persisted through the `BackupRepository` abstraction
(`repositories/backup_repository.py`), implemented by `SQLAlchemyBackupRepository`, with the
`DeviceBackup` domain entity (`domain/entities/device_backup.py`) holding the decrypted snapshot.

Two more use cases drive scheduled backups:

- **ManageBackupSchedulesUseCase** - CRUD plus enable/disable for `BackupSchedule` entities
  (`domain/entities/backup_schedule.py`), persisted via `BackupScheduleRepository`.
- **RunDueBackupsUseCase** - resolves a schedule's targets, captures a backup of each, and applies
  the retention policy. It takes an injectable clock so the runner is deterministic under test, and
  opens its own repository sessions because it runs outside any HTTP request. Retention is scoped to
  scheduled snapshots, so a manual backup is never pruned by a schedule.

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
