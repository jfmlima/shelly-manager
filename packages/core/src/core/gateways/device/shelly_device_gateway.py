"""
Device gateway implementation for Shelly devices.
"""

import asyncio
from datetime import datetime
from typing import Any

from ...domain.entities.exceptions import (
    DeviceAuthenticationError,
    DeviceCommunicationError,
)
from ...domain.entities.shelly_device import ShellyDevice
from ...domain.enums.enums import DeviceStatus
from ...domain.value_objects.action_result import ActionResult
from .device import DeviceGateway


class ShellyDeviceGateway(DeviceGateway):

    def __init__(self, rpc_client: Any) -> None:
        self._rpc_client = rpc_client

    async def discover_device(
        self, ip: str, timeout: float = 3.0
    ) -> ShellyDevice | None:
        try:
            device_info, response_time = await self._rpc_client.make_rpc_request(
                ip, "Shelly.GetDeviceInfo", timeout=timeout
            )

            return ShellyDevice(
                ip=ip,
                status=DeviceStatus.DETECTED,
                device_id=device_info.get("id"),
                device_type=device_info.get("model"),
                device_name=device_info.get("name"),
                firmware_version=device_info.get("fw_id"),
                response_time=response_time,
                last_seen=datetime.now(),
            )

        except Exception as e:
            return ShellyDevice(
                ip=ip,
                status=DeviceStatus.UNREACHABLE,
                error_message=str(e),
                last_seen=datetime.now(),
            )

    async def get_device_status(
        self, ip: str, include_updates: bool = True
    ) -> ShellyDevice | None:
        try:
            device = await self.discover_device(ip)
            if not device or device.status != DeviceStatus.DETECTED:
                return device

            if include_updates:
                try:
                    update_info, _ = await self._rpc_client.make_rpc_request(
                        ip, "Shelly.CheckForUpdate"
                    )

                    stable_update = update_info.get("stable", {}) if update_info else {}
                    beta_update = update_info.get("beta", {}) if update_info else {}

                    if stable_update.get("version") or beta_update.get("version"):
                        device.status = DeviceStatus.UPDATE_AVAILABLE

                except Exception:
                    pass

            return device

        except Exception as e:
            return ShellyDevice(
                ip=ip,
                status=DeviceStatus.ERROR,
                error_message=str(e),
                last_seen=datetime.now(),
            )

    async def execute_action(
        self, ip: str, action_type: str, parameters: dict[str, Any]
    ) -> ActionResult:

        try:
            if action_type == "update":
                return await self._execute_update(ip, parameters)
            elif action_type == "reboot":
                return await self._execute_reboot(ip)
            elif action_type == "config-get":
                return await self._execute_config_get(ip)
            elif action_type == "config-set":
                return await self._execute_config_set(ip, parameters)
            else:
                return ActionResult(
                    device_ip=ip,
                    action_type=action_type,
                    success=False,
                    message=f"Unknown action type: {action_type}",
                    error=f"Unknown action type: {action_type}",
                )

        except Exception as e:
            err = str(e)
            if "401" in err or "unauthorized" in err.lower():
                error_message = DeviceAuthenticationError(ip, err).message
            else:
                error_message = DeviceCommunicationError(ip, err, err).message

            return ActionResult(
                device_ip=ip,
                action_type=action_type,
                success=False,
                message=f"Action failed: {err}",
                error=error_message,
            )

    async def _execute_update(
        self, ip: str, parameters: dict[str, Any]
    ) -> ActionResult:
        try:
            await self._rpc_client.make_rpc_request(ip, "Shelly.Update")

            return ActionResult(
                device_ip=ip,
                action_type="update",
                success=True,
                message="Update initiated successfully",
            )
        except Exception as e:
            return ActionResult(
                device_ip=ip,
                action_type="update",
                success=False,
                message=f"Update failed: {str(e)}",
                error=str(e),
            )

    async def _execute_reboot(self, ip: str) -> ActionResult:
        try:
            await self._rpc_client.make_rpc_request(ip, "Sys.Reboot")

            return ActionResult(
                device_ip=ip,
                action_type="reboot",
                success=True,
                message="Reboot initiated successfully",
            )
        except Exception as e:
            return ActionResult(
                device_ip=ip,
                action_type="reboot",
                success=False,
                message=f"Reboot failed: {str(e)}",
                error=str(e),
            )

    async def _execute_config_get(self, ip: str) -> ActionResult:
        try:
            config, _ = await self._rpc_client.make_rpc_request(ip, "Sys.GetConfig")

            return ActionResult(
                device_ip=ip,
                action_type="config-get",
                success=True,
                message="Configuration retrieved successfully",
                data=config,
            )
        except Exception as e:
            return ActionResult(
                device_ip=ip,
                action_type="config-get",
                success=False,
                message=f"Configuration retrieval failed: {str(e)}",
                error=str(e),
            )

    async def _execute_config_set(
        self, ip: str, parameters: dict[str, Any]
    ) -> ActionResult:
        try:
            config_data = parameters.get("config", {})
            if not config_data:
                raise ValueError("No configuration data provided")

            await self._rpc_client.make_rpc_request(
                ip, "Sys.SetConfig", params={"config": config_data}
            )

            return ActionResult(
                device_ip=ip,
                action_type="config-set",
                success=True,
                message="Configuration updated successfully",
            )
        except Exception as e:
            return ActionResult(
                device_ip=ip,
                action_type="config-set",
                success=False,
                message=f"Configuration update failed: {str(e)}",
                error=str(e),
            )

    async def execute_bulk_action(
        self, device_ips: list[str], action_type: str, parameters: dict[str, Any]
    ) -> list[ActionResult]:
        tasks = [self.execute_action(ip, action_type, parameters) for ip in device_ips]
        return await asyncio.gather(*tasks, return_exceptions=False)

    async def get_device_config(self, ip: str) -> dict[str, Any] | None:
        try:
            config, _ = await self._rpc_client.make_rpc_request(ip, "Sys.GetConfig")
            if isinstance(config, dict):
                return config
            return None
        except Exception:
            return None

    async def set_device_config(self, ip: str, config: dict[str, Any]) -> bool:
        try:
            await self._rpc_client.make_rpc_request(
                ip, "Sys.SetConfig", params={"config": config}
            )
            return True
        except Exception:
            return False
