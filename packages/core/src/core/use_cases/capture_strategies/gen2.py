"""Capture strategy for Gen2+ (RPC) devices."""

from typing import Any

from core.domain.entities.device_status import DeviceStatus
from core.gateways.device import DeviceGateway


class Gen2CaptureStrategy:
    """Capture component configs over the Gen2+ RPC surface."""

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def capture_components(
        self, device_ip: str, status: DeviceStatus, component_types: list[str]
    ) -> dict[str, Any]:
        components: dict[str, Any] = {}

        for component in status.components:
            if component.component_type in component_types:

                config_result = await self._device_gateway.execute_component_action(
                    device_ip, component.key, "GetConfig", {}
                )

                component_export = {
                    "type": component.component_type,
                    "success": config_result.success,
                    "config": config_result.data if config_result.success else None,
                    "error": (
                        config_result.error if not config_result.success else None
                    ),
                }

                if component.component_type == "script" and config_result.success:
                    code_data = await self._fetch_script_code(device_ip, component.key)
                    if code_data is not None:
                        component_export["code"] = code_data

                components[component.key] = component_export

        if "schedules" in component_types:
            schedules = await self._fetch_schedules(device_ip)
            components.update(schedules)

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

    async def _fetch_schedules(self, device_ip: str) -> dict[str, Any]:
        schedule_export = {}

        list_result = await self._device_gateway.execute_component_action(
            device_ip, "schedule", "List", {}
        )
        schedule_data = list_result.data
        if list_result.success and schedule_data:
            schedule_export["schedules"] = {
                "type": "schedule",
                "success": True,
                "config": schedule_data,
                "error": None,
            }
        elif not list_result.success:
            schedule_export["schedules"] = {
                "type": "schedule",
                "success": False,
                "config": None,
                "error": list_result.error,
            }

        return schedule_export
