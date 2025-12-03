"""
Device gateway implementation for Shelly devices.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from ...domain.entities.device_status import DeviceStatus
from ...domain.entities.discovered_device import DiscoveredDevice
from ...domain.entities.exceptions import (
    DeviceAuthenticationError,
    DeviceCommunicationError,
)
from ...domain.enums.enums import Status
from ...domain.value_objects.action_result import ActionResult
from .component_type_mapping import get_api_component_type
from .device import DeviceGateway
from .legacy_device_gateway import LegacyDeviceGateway

logger = logging.getLogger(__name__)

SHELLY_SYSTEM_ACTIONS = {"Update", "Reboot", "FactoryReset"}


class ShellyDeviceGateway(DeviceGateway):

    def __init__(
        self,
        rpc_client: Any,
        timeout: float = 10.0,
        legacy_gateway: LegacyDeviceGateway | None = None,
    ) -> None:
        self._rpc_client = rpc_client
        self.timeout = timeout
        self._legacy_gateway = legacy_gateway

    async def discover_device(self, ip: str) -> DiscoveredDevice | None:
        """
        Discover basic device information (original get_device_status logic).

        Args:
            ip: Device IP address

        Returns:
            DiscoveredDevice with basic info and update status, or None if unreachable
        """
        try:
            device_info, response_time = await self._rpc_client.make_rpc_request(
                ip, "Shelly.GetDeviceInfo", timeout=self.timeout
            )
            device_data = device_info.get("result", device_info)

            device = DiscoveredDevice(
                ip=ip,
                status=Status.DETECTED,
                device_id=device_data.get("id"),
                device_type=device_data.get("model"),
                device_name=device_data.get("name"),
                firmware_version=device_data.get("fw_id"),
                response_time=response_time,
                last_seen=datetime.now(),
            )

            try:
                update_info, _ = await self._rpc_client.make_rpc_request(
                    ip, "Shelly.CheckForUpdate", timeout=self.timeout
                )
                update_data = update_info.get("result", update_info)

                stable_update = update_data.get("stable", {}) if update_data else {}
                beta_update = update_data.get("beta", {}) if update_data else {}

                if stable_update.get("version") or beta_update.get("version"):
                    device.status = Status.UPDATE_AVAILABLE
                else:
                    device.status = Status.NO_UPDATE_NEEDED

            except Exception as e:
                logger.error(f"Error checking for updates: {e}", exc_info=True)
                pass

            return device

        except Exception as e:
            logger.debug(
                "RPC discovery failed for %s, attempting legacy HTTP fallback: %s",
                ip,
                e,
            )
            if self._legacy_gateway:
                legacy_device = await self._legacy_gateway.discover_device(ip)
                if legacy_device:
                    return legacy_device

            return DiscoveredDevice(
                ip=ip,
                status=Status.UNREACHABLE,
                error_message=str(e),
                last_seen=datetime.now(),
            )

    async def get_device_status(self, ip: str) -> DeviceStatus | None:
        """
        Get device components and detailed status information.

        Args:
            ip: Device IP address

        Returns:
            DeviceStatus with all component data, or None if unreachable
        """
        try:
            rpc_success = False
            device_info_data = None
            try:
                device_info_response, _ = await self._rpc_client.make_rpc_request(
                    ip, "Shelly.GetDeviceInfo", timeout=self.timeout
                )
                device_info_data = device_info_response.get(
                    "result", device_info_response
                )
                rpc_success = True
            except Exception as e:
                logger.error(f"Error getting device info: {e}", exc_info=True)

            components_data = {}
            try:
                components_response, _ = await self._rpc_client.make_rpc_request(
                    ip,
                    "Shelly.GetComponents",
                    params={"offset": 0},
                    timeout=self.timeout,
                )
                components_data = components_response.get("result", components_response)
                rpc_success = True
            except Exception as e:
                logger.error(f"Error getting components: {e}", exc_info=True)

            status_response = None
            try:
                status_response, _ = await self._rpc_client.make_rpc_request(
                    ip, "Shelly.GetStatus", timeout=self.timeout
                )
                status_response = status_response.get("result", status_response)
                rpc_success = True
            except Exception as e:
                logger.error(f"Error getting device status: {e}", exc_info=True)

            available_methods = await self.get_available_methods(ip)

            if not rpc_success:
                raise RuntimeError("RPC status retrieval failed; use legacy path")

            return DeviceStatus.from_raw_response(
                ip,
                components_data,
                available_methods=available_methods,
                device_info_data=device_info_data,
                status_data=status_response,
            )

        except Exception as e:
            logger.error(
                f"Error getting device status via RPC, attempting legacy fallback: {e}",
                exc_info=True,
            )
            if self._legacy_gateway:
                legacy_status = await self._legacy_gateway.get_device_status(ip)
                if legacy_status:
                    return legacy_status
            return None

    async def get_available_methods(self, ip: str) -> list[str]:
        """Get available RPC methods for action validation.

        Args:
            ip: Device IP address

        Returns:
            List of available RPC method names, empty list on failure
        """
        try:
            methods_response, _ = await self._rpc_client.make_rpc_request(
                ip, "Shelly.ListMethods", timeout=self.timeout
            )
            result = methods_response.get("result", methods_response)
            if isinstance(result, dict) and "methods" in result:
                methods = result["methods"]

                return methods if isinstance(methods, list) else []

            return []
        except Exception as e:
            logger.warning(f"Failed to get available methods for {ip}: {e}")
            return []

    async def execute_component_action(
        self,
        ip: str,
        component_key: str,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> ActionResult:
        """Execute validated action on any component type.

        Args:
            ip: Device IP address
            component_key: Component key (e.g., 'switch:0', 'sys', 'zigbee')
            action: Action name (e.g., 'Toggle', 'Reboot', 'Update')
            parameters: Action-specific parameters (e.g., {'channel': 'beta'})

        Returns:
            ActionResult with success/failure details
        """
        try:
            if action.startswith("Legacy."):
                if self._legacy_gateway:
                    return await self._legacy_gateway.execute_action(
                        ip, component_key, action, parameters or {}
                    )
                else:
                    return ActionResult(
                        device_ip=ip,
                        action_type=f"{component_key}.{action}",
                        success=False,
                        message="Legacy gateway not available",
                        error="Legacy operations require legacy gateway injection",
                    )

            available_methods = await self.get_available_methods(ip)
            rpc_method = self._build_rpc_method_name(component_key, action)

            if available_methods and rpc_method not in available_methods:
                return ActionResult(
                    device_ip=ip,
                    action_type=f"{component_key}.{action}",
                    success=False,
                    message=f"Action {rpc_method} not supported by device",
                    error=f"Method {rpc_method} not found in available methods",
                )

            params: dict[str, Any] = {}
            if ":" in component_key and component_key != "sys":
                try:
                    component_id = int(component_key.split(":")[1])
                    params["id"] = component_id
                except (IndexError, ValueError):
                    return ActionResult(
                        device_ip=ip,
                        action_type=f"{component_key}.{action}",
                        success=False,
                        message=f"Invalid component key format: {component_key}",
                        error=f"Could not parse component ID from {component_key}",
                    )

            if parameters:
                params.update(parameters)

            rpc_params: dict[str, Any] | None = params if params else None
            response, _ = await self._rpc_client.make_rpc_request(
                ip, rpc_method, params=rpc_params, timeout=self.timeout
            )

            return ActionResult(
                device_ip=ip,
                action_type=f"{component_key}.{action}",
                success=True,
                message=f"{action} executed successfully on {component_key}",
                data=response,
            )

        except Exception as e:
            err = str(e)
            if "401" in err or "unauthorized" in err.lower():
                error_message = DeviceAuthenticationError(ip, err).message
            else:
                error_message = DeviceCommunicationError(ip, err, err).message

            return ActionResult(
                device_ip=ip,
                action_type=f"{component_key}.{action}",
                success=False,
                message=f"Action failed: {err}",
                error=error_message,
            )

    def _build_rpc_method_name(self, component_key: str, action: str) -> str:
        """Build RPC method name from component key and action.

        Args:
            component_key: Component key (e.g., 'switch:0', 'sys', 'zigbee')
            action: Action name (e.g., 'Toggle', 'Reboot', 'Update')

        Returns:
            RPC method name (e.g., 'Switch.Toggle', 'Shelly.Reboot', 'Shelly.Update', 'Sys.GetConfig')
        """
        component_type = (
            component_key.split(":")[0] if ":" in component_key else component_key
        )
        component_prefix = get_api_component_type(component_type)

        return f"{component_prefix}.{action}"

    async def execute_bulk_action(
        self,
        device_ips: list[str],
        component_key: str,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[ActionResult]:
        """Execute component actions on multiple devices in parallel.

        Only supports specific bulk operations:
        - shelly.Update: Firmware updates
        - shelly.Reboot: Device reboot
        - shelly.FactoryReset: Factory reset

        Args:
            device_ips: List of device IP addresses
            component_key: Component key (must be 'shelly' for bulk operations)
            action: Action name (Update, Reboot, FactoryReset)

        Returns:
            List of ActionResult objects

        Raises:
            ValueError: If component_key/action combination is not supported for bulk operations
        """
        allowed_bulk_operations = SHELLY_SYSTEM_ACTIONS

        if action not in allowed_bulk_operations and component_key.lower() != "shelly":
            raise ValueError(
                f"Bulk operation '{component_key}.{action}' is not supported. "
                f"Supported operations: shelly.Update, shelly.Reboot, shelly.FactoryReset"
            )

        tasks = [
            self.execute_component_action(ip, component_key, action, parameters)
            for ip in device_ips
        ]

        return await asyncio.gather(*tasks, return_exceptions=False)
