"""Per-generation restore strategies.

``RestoreDeviceConfig`` owns orchestration (selection, ordering, identity,
aggregation); everything a generation does differently on the wire lives behind
``ComponentRestoreStrategy``.
"""

from dataclasses import dataclass, field
from typing import Protocol

from core.domain.entities.config_snapshot import ComponentSnapshot, DeviceSnapshot
from core.domain.entities.device_status import DeviceStatus
from core.domain.value_objects.restore_result import ComponentRestoreResult


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
        self, device_ip: str, snapshot: DeviceSnapshot, status: DeviceStatus
    ) -> PrepareOutcome: ...

    async def restore_component(
        self,
        device_ip: str,
        entry: ComponentSnapshot,
        present_keys: set[str],
    ) -> ComponentRestoreResult: ...

    async def reboot(self, device_ip: str) -> None: ...
