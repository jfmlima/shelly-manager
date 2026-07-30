"""Per-generation capture strategies.

The capture mirror of :mod:`core.use_cases.restore_strategies`:
``CaptureDeviceConfig`` owns the snapshot envelope and picks the strategy; how
one generation's component configs come off the wire lives behind
``ComponentCaptureStrategy``.
"""

from typing import Protocol

from core.domain.entities.config_snapshot import ComponentSnapshot
from core.domain.entities.device_status import DeviceStatus


class ComponentCaptureStrategy(Protocol):
    """One device generation's side of a config capture."""

    async def capture_components(
        self, device_ip: str, status: DeviceStatus, component_types: list[str]
    ) -> dict[str, ComponentSnapshot]:
        """Captured component entries keyed by component key.

        A key absent from the result was never captured, which restore reports
        differently from a key captured with ``success=False``.
        """
        ...
