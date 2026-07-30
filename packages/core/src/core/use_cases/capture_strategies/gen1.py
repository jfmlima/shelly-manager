"""Capture strategy for Gen1 (legacy HTTP) devices."""

from core.domain.entities.config_snapshot import LEGACY_SETTINGS_KEY, ComponentSnapshot
from core.domain.entities.device_status import DeviceStatus
from core.gateways.device import DeviceGateway


class Gen1CaptureStrategy:
    """Capture Gen1 component configs plus the raw ``/settings``.

    Gen1 has no /rpc: GetConfig and Schedule.List 404, so the mapped configs
    already on the ``DeviceStatus`` are captured instead. The
    ``legacy_settings`` entry is the source of truth a Gen1 restore replays, and
    it is omitted when the raw fetch fails. Capture reports that omission rather
    than judging it; whether a snapshot without it is worth storing is the
    caller's call (``BackupDeviceConfig`` refuses, since it could not restore).
    """

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def capture_components(
        self, device_ip: str, status: DeviceStatus, component_types: list[str]
    ) -> dict[str, ComponentSnapshot]:
        components: dict[str, ComponentSnapshot] = {}

        for component in status.components:
            if component.component_type in component_types:
                components[component.key] = ComponentSnapshot(
                    key=component.key,
                    component_type=component.component_type,
                    success=True,
                    config=component.config,
                )

        legacy_settings = await self._device_gateway.get_legacy_settings(device_ip)
        if legacy_settings is not None:
            components[LEGACY_SETTINGS_KEY] = ComponentSnapshot(
                key=LEGACY_SETTINGS_KEY,
                component_type=LEGACY_SETTINGS_KEY,
                success=True,
                config=legacy_settings,
            )

        return components
