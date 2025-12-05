from datetime import UTC, datetime
from typing import Any

from ..domain.entities.device_status import DeviceStatus
from ..domain.entities.exceptions import BulkOperationError
from ..domain.value_objects.action_result import ActionResult
from ..gateways.device import DeviceGateway


class BulkOperationsUseCase:

    def __init__(
        self,
        device_gateway: DeviceGateway,
    ):
        self._device_gateway = device_gateway

    async def execute_bulk_update(
        self, device_ips: list[str], channel: str = "stable"
    ) -> list[ActionResult]:
        """
        Update firmware on multiple devices.

        Args:
            device_ips: List of device IP addresses
            channel: Update channel (stable/beta)

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "shelly", "Update", {"channel": channel}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_update", device_ips, f"Bulk update failed: {str(e)}"
            ) from e

    async def execute_bulk_reboot(self, device_ips: list[str]) -> list[ActionResult]:
        """
        Reboot multiple devices.

        Args:
            device_ips: List of device IP addresses

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "shelly", "Reboot", {}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_reboot", device_ips, f"Bulk reboot failed: {str(e)}"
            ) from e

    async def execute_bulk_factory_reset(
        self, device_ips: list[str]
    ) -> list[ActionResult]:
        """
        Factory reset multiple devices.

        Args:
            device_ips: List of device IP addresses

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "shelly", "FactoryReset", {}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_factory_reset", device_ips, f"Bulk factory reset failed: {str(e)}"
            ) from e

    async def get_bulk_status(
        self, device_ips: list[str], include_updates: bool = True
    ) -> list[DeviceStatus]:
        """
        Get status of multiple devices.

        Args:
            device_ips: List of device IP addresses
            include_updates: Include update information (parameter kept for compatibility but not used)

        Returns:
            List of device statuses
        """
        results = []

        for ip in device_ips:
            try:
                device = await self._device_gateway.get_device_status(ip)
                if device:
                    results.append(device)
            except Exception as e:
                print(f"Error getting status for {ip}: {str(e)}")

        return results

    async def export_bulk_config(
        self,
        device_ips: list[str],
        component_types: list[str],
    ) -> dict[str, Any]:
        """
        Export component configurations organized per device.

        Args:
            device_ips: List of device IP addresses
            component_types: List of component types to export

        Returns:
            Dictionary containing export metadata and device configurations
        """
        result = {
            "export_metadata": {
                "timestamp": datetime.now(UTC).isoformat() + "Z",
                "total_devices": len(device_ips),
                "component_types": component_types,
            },
            "devices": {},
        }

        for device_ip in device_ips:

            device_status = await self._device_gateway.get_device_status(device_ip)
            if not device_status:
                continue

            device_data: dict[str, Any] = {
                "device_info": {
                    "device_name": device_status.device_name,
                    "device_type": device_status.device_type,
                    "firmware_version": device_status.firmware_version,
                    "mac_address": device_status.mac_address,
                    "app_name": device_status.app_name,
                },
                "components": {},
            }

            for component in device_status.components:
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
                        code_data = await self._fetch_script_code(
                            device_ip, component.key
                        )
                        if code_data is not None:
                            component_export["code"] = code_data

                    device_data["components"][component.key] = component_export

            if "schedules" in component_types:
                schedules = await self._fetch_schedules(device_ip)
                device_data["components"].update(schedules)

            result["devices"][device_ip] = device_data

        return result

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

    async def apply_bulk_config(
        self,
        device_ips: list[str],
        component_type: str,
        config: dict[str, Any],
    ) -> list[ActionResult]:
        """
        Apply component configuration to multiple devices.

        Args:
            device_ips: List of device IP addresses
            component_type: Type of component to apply configuration to
            config: Configuration to apply

        Returns:
            List of action results
        """
        all_results = []

        for device_ip in device_ips:
            result = await self._device_gateway.execute_component_action(
                device_ip, component_type, "SetConfig", {"config": config}
            )
            all_results.append(result)

        return all_results
