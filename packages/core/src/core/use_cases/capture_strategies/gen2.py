"""Capture strategy for Gen2+ (RPC) devices."""

from typing import Any

from core.domain.entities.config_snapshot import SCHEDULES_KEY, ComponentSnapshot
from core.domain.entities.device_status import DeviceStatus
from core.gateways.device import DeviceGateway

# The RPC component behind the "schedules" snapshot entry.
SCHEDULE_COMPONENT = "schedule"


class Gen2CaptureStrategy:
    """Capture component configs over the Gen2+ RPC surface."""

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def capture_components(
        self, device_ip: str, status: DeviceStatus, component_types: list[str]
    ) -> dict[str, ComponentSnapshot]:
        components: dict[str, ComponentSnapshot] = {}

        for component in status.components:
            if component.component_type in component_types:

                config_result = await self._device_gateway.execute_component_action(
                    device_ip, component.key, "GetConfig", {}
                )

                code = None
                if component.component_type == "script" and config_result.success:
                    code = await self._fetch_script_code(device_ip, component.key)

                components[component.key] = ComponentSnapshot(
                    key=component.key,
                    component_type=component.component_type,
                    success=config_result.success,
                    config=config_result.data if config_result.success else None,
                    error=config_result.error if not config_result.success else None,
                    code=code,
                )

        if SCHEDULES_KEY in component_types:
            schedules = await self._fetch_schedules(device_ip)
            if schedules is not None:
                components[SCHEDULES_KEY] = schedules

        return components

    async def _fetch_script_code(
        self, device_ip: str, component_key: str
    ) -> dict[str, Any] | None:
        try:
            script_id = int(component_key.split(":")[1])
            code_result = await self._device_gateway.execute_component_action(
                device_ip, component_key, "GetCode", {"id": script_id}
            )
            if code_result.success and code_result.data:
                return code_result.data
        except (ValueError, IndexError, AttributeError):
            pass

        return None

    async def _fetch_schedules(self, device_ip: str) -> ComponentSnapshot | None:
        """Capture the device's schedule jobs.

        Returns ``None`` when the listing succeeded but came back empty: that
        leaves the entry out of the snapshot entirely, which restore reports
        differently from a listing that failed.
        """
        list_result = await self._device_gateway.execute_component_action(
            device_ip, SCHEDULE_COMPONENT, "List", {}
        )
        schedule_data = list_result.data
        if list_result.success and schedule_data:
            return ComponentSnapshot(
                key=SCHEDULES_KEY,
                component_type=SCHEDULE_COMPONENT,
                success=True,
                config=schedule_data,
            )
        if not list_result.success:
            return ComponentSnapshot(
                key=SCHEDULES_KEY,
                component_type=SCHEDULE_COMPONENT,
                success=False,
                error=list_result.error,
            )
        return None
