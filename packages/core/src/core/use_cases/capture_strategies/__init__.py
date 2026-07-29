"""Per-generation capture strategies.

The capture mirror of :mod:`core.use_cases.restore_strategies`:
``BulkOperationsUseCase.export_bulk_config`` owns the export envelope and the
per-device loop; how one generation's component configs are captured lives
behind ``ComponentCaptureStrategy``.
"""

from typing import Any, Protocol

from core.domain.entities.device_status import DeviceStatus


class ComponentCaptureStrategy(Protocol):
    """One device generation's side of a config capture."""

    async def capture_components(
        self, device_ip: str, status: DeviceStatus, component_types: list[str]
    ) -> dict[str, Any]:
        """Captured component entries keyed by component key, in the snapshot
        shape (``{"type", "success", "config", "error"}`` plus per-type
        extras)."""
        ...
