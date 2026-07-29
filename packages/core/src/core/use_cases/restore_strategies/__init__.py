"""Per-generation restore strategies.

``RestoreDeviceConfig`` owns orchestration (selection, ordering, identity,
aggregation); everything a generation does differently on the wire lives behind
``ComponentRestoreStrategy``.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol

from core.domain.entities.device_backup import DeviceBackup
from core.domain.entities.device_status import DeviceStatus
from core.domain.value_objects.restore_result import ComponentRestoreResult

# The raw Gen1 /settings entry captured alongside the mapped components. It is the
# data source a Gen1 restore replays, never a restore target itself.
LEGACY_SETTINGS_KEY = "legacy_settings"


@dataclass
class PrepareOutcome:
    """Result of a strategy's pre-restore phase.

    ``status`` is the device status to restore against (Gen1 re-reads it after
    a mode change). ``preliminary`` carries component results produced before
    the component loop (the Gen1 mode entry); a failed, non-skipped preliminary
    result aborts the restore with exactly those results. ``abort_reason`` is
    set when the snapshot cannot be restored at all (e.g. it lacks raw Gen1
    settings): the restore reports every selected component as skipped for that
    reason.
    """

    status: DeviceStatus
    preliminary: list[ComponentRestoreResult] = field(default_factory=list)
    abort_reason: str | None = None


class ComponentRestoreStrategy(Protocol):
    """One device generation's side of a restore."""

    async def prepare(
        self, device_ip: str, backup: DeviceBackup, status: DeviceStatus
    ) -> PrepareOutcome: ...

    async def restore_component(
        self,
        device_ip: str,
        key: str,
        entry: dict[str, Any],
        present_keys: set[str],
    ) -> ComponentRestoreResult: ...

    async def reboot(self, device_ip: str) -> None: ...
