"""The device configuration snapshot: one shape capture writes and restore reads.

A snapshot is the per-device block of a bulk export and, byte for byte, the
payload stored on a :class:`~core.domain.entities.device_backup.DeviceBackup`.
``to_dict`` and ``from_dict`` are the only place its on-disk key names live, so
producers and consumers agree on one shape instead of probing untyped dicts.

Stored snapshots outlive the code that wrote them, so ``from_dict`` is lenient:
missing or malformed entries degrade to "nothing captured" rather than raising.
"""

from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any

from ..services.gen1_settings_translation import without_identity
from ..value_objects.component_namespace import known_component_types
from .device_status import DeviceStatus

# The raw Gen1 /settings entry captured alongside the mapped components. It is
# the data source a Gen1 restore replays, never a restore target itself.
LEGACY_SETTINGS_KEY = "legacy_settings"

# The pseudo-component holding a Gen2+ device's schedule jobs.
SCHEDULES_KEY = "schedules"

# "shelly" and "schedule" route actions and kvs/http/webhook are services, so
# none of them owns an exportable config. Capture skips types a device does not
# have, so the set can be broader than any one device.
EXPORTABLE_COMPONENT_TYPES: frozenset[str] = (
    known_component_types() - {"shelly", "schedule", "kvs", "http", "webhook"}
) | {SCHEDULES_KEY}

# Schedules are replayed by restore rather than applied via SetConfig, and the
# energy data logs own no settable configuration.
CONFIGURABLE_COMPONENT_TYPES: frozenset[str] = EXPORTABLE_COMPONENT_TYPES - {
    SCHEDULES_KEY,
    "emdata",
    "em1data",
}

NETWORK_TYPES: frozenset[str] = frozenset({"wifi", "eth", "mqtt", "ws", "cloud"})

# Gen2+ config paths that name one physical device, by component type. Both MQTT
# ids default to the device id; two devices sharing them fight over the broker.
GEN2_IDENTITY_PATHS: dict[str, tuple[tuple[str, ...], ...]] = {
    "sys": (("device", "name"),),
    "mqtt": (("client_id",), ("topic_prefix",)),
}


@dataclass(frozen=True)
class SnapshotDeviceInfo:
    """The device identity captured alongside the component configs."""

    device_name: str | None = None
    device_type: str | None = None
    firmware_version: str | None = None
    mac_address: str | None = None
    app_name: str | None = None

    @classmethod
    def from_status(cls, status: DeviceStatus) -> "SnapshotDeviceInfo":
        return cls(
            device_name=status.device_name,
            device_type=status.device_type,
            firmware_version=status.firmware_version,
            mac_address=status.mac_address,
            app_name=status.app_name,
        )

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "SnapshotDeviceInfo":
        return cls(
            device_name=raw.get("device_name"),
            device_type=raw.get("device_type"),
            firmware_version=raw.get("firmware_version"),
            mac_address=raw.get("mac_address"),
            app_name=raw.get("app_name"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_name": self.device_name,
            "device_type": self.device_type,
            "firmware_version": self.firmware_version,
            "mac_address": self.mac_address,
            "app_name": self.app_name,
        }


@dataclass(frozen=True)
class ComponentSnapshot:
    """One captured component: its config plus how the capture went.

    ``code`` belongs to scripts alone and only survives when the code fetch
    succeeded, so it is absent from the serialized form for everything else.
    """

    key: str
    component_type: str | None = None
    success: bool = False
    config: dict[str, Any] | None = None
    error: str | None = None
    code: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, key: str, raw: Any) -> "ComponentSnapshot":
        """Read one stored entry.

        An entry that is not a mapping is corrupt, not absent: it comes back as
        a failed capture so a restore still reports the key rather than quietly
        handing the caller a smaller selection than they asked for.
        """
        if not isinstance(raw, dict):
            return cls(key=key, success=False, error="unreadable snapshot entry")
        return cls(
            key=key,
            component_type=raw.get("type"),
            success=bool(raw.get("success")),
            config=raw.get("config"),
            error=raw.get("error"),
            code=raw.get("code"),
        )

    def to_dict(self) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "type": self.component_type,
            "success": self.success,
            "config": self.config,
            "error": self.error,
        }
        if self.code is not None:
            entry["code"] = self.code
        return entry

    @property
    def script_code(self) -> str | None:
        """The script body captured for this component, if any.

        Presence and type, not truthiness: an empty script body ("") is a
        valid capture.
        """
        if not isinstance(self.code, dict):
            return None
        code = self.code.get("data")
        return code if isinstance(code, str) else None

    @property
    def has_restorable_payload(self) -> bool:
        """True if this entry carries something a restore could apply.

        Scripts count only once their code was actually fetched: GetConfig
        succeeding is not enough, since restore re-pushes ``code.data``.
        """
        if self.component_type == "script":
            return self.script_code is not None
        return bool(self.success and self.config is not None)


@dataclass(frozen=True)
class DeviceSnapshot:
    """A full configuration capture of a single device."""

    device_info: SnapshotDeviceInfo = field(default_factory=SnapshotDeviceInfo)
    components: dict[str, ComponentSnapshot] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "DeviceSnapshot":
        info = raw.get("device_info")
        components = raw.get("components")
        return cls(
            device_info=SnapshotDeviceInfo.from_dict(
                info if isinstance(info, dict) else {}
            ),
            components={
                key: ComponentSnapshot.from_dict(key, entry)
                for key, entry in (
                    components if isinstance(components, dict) else {}
                ).items()
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_info": self.device_info.to_dict(),
            "components": {
                key: entry.to_dict() for key, entry in self.components.items()
            },
        }

    @property
    def has_restorable_payload(self) -> bool:
        """True if any captured component carries something restorable."""
        return any(entry.has_restorable_payload for entry in self.components.values())

    @property
    def legacy_settings(self) -> dict[str, Any] | None:
        """The raw Gen1 /settings a Gen1 restore replays, if it was captured."""
        entry = self.components.get(LEGACY_SETTINGS_KEY)
        if entry is None or not entry.success:
            return None
        return entry.config if isinstance(entry.config, dict) else None


def without_device_identity(snapshot: DeviceSnapshot) -> DeviceSnapshot:
    """A copy of ``snapshot`` without the keys that name the captured device.

    Used when the backup is restored onto another device, which keeps its own
    name and MQTT ids. Every other key, and ``snapshot`` itself, is unchanged.
    """
    return replace(
        snapshot,
        components={
            key: _without_identity(entry) for key, entry in snapshot.components.items()
        },
    )


def _without_identity(entry: ComponentSnapshot) -> ComponentSnapshot:
    if not isinstance(entry.config, dict):
        return entry
    if entry.key == LEGACY_SETTINGS_KEY:
        return replace(entry, config=without_identity(entry.config))
    paths = GEN2_IDENTITY_PATHS.get(entry.component_type or "")
    if paths is None:
        return entry
    config = deepcopy(entry.config)
    for path in paths:
        _pop_path(config, path)
    return replace(entry, config=config)


def _pop_path(config: dict[str, Any], path: tuple[str, ...]) -> None:
    *parents, leaf = path
    section: Any = config
    for part in parents:
        section = section.get(part)
        if not isinstance(section, dict):
            return
    section.pop(leaf, None)
