"""Device configuration backup domain entities."""

from dataclasses import dataclass, field
from typing import Any

from core.utils.validation import normalize_mac


@dataclass
class DeviceBackup:
    """A full configuration snapshot of a single Shelly device.

    The ``snapshot`` holds the decrypted capture for one device, serialized by
    :class:`~core.domain.entities.config_snapshot.DeviceSnapshot`; parse it
    back through that type rather than reading its keys by hand.
    """

    device_mac: str
    snapshot: dict[str, Any] = field(default_factory=dict)
    device_ip: str | None = None
    device_name: str | None = None
    device_type: str | None = None
    firmware_version: str | None = None
    generation: str = "gen2"
    name: str | None = None
    source: str = "manual"
    sha256: str | None = None
    size_bytes: int = 0
    id: int | None = None
    created_at: int | None = None

    def __post_init__(self) -> None:
        self.device_mac = normalize_mac(self.device_mac)


@dataclass
class DeviceBackupSummary:
    """Lightweight backup record without the (encrypted) snapshot blob.

    Used for list views so they don't decrypt every snapshot; listing keeps
    working even after the encryption key has rotated.
    """

    device_mac: str
    id: int | None = None
    device_ip: str | None = None
    device_name: str | None = None
    device_type: str | None = None
    firmware_version: str | None = None
    generation: str = "gen2"
    name: str | None = None
    source: str = "manual"
    sha256: str | None = None
    size_bytes: int = 0
    created_at: int | None = None

    def __post_init__(self) -> None:
        self.device_mac = normalize_mac(self.device_mac)


@dataclass
class BackupPage:
    """A single page of backup summaries plus the total matching count.

    ``total`` is the full number of backups matching the query (ignoring the
    page window), so a client can render "showing N of total" and decide
    whether more pages exist.
    """

    items: list[DeviceBackupSummary] = field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0
