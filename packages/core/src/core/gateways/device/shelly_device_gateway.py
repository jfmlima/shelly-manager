"""
Device gateway implementation for Shelly devices.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, cast

import requests

from ...domain.entities.device_status import DeviceStatus
from ...domain.entities.discovered_device import DiscoveredDevice
from ...domain.entities.exceptions import (
    DeviceAuthenticationError,
    DeviceCommunicationError,
)
from ...domain.enums.enums import Status
from ...domain.value_objects.action_result import ActionResult
from .device import DeviceGateway
from .legacy_component_mapper import LegacyComponentMapper

logger = logging.getLogger(__name__)

SHELLY_SYSTEM_ACTIONS = {"Update", "Reboot", "FactoryReset"}


class ShellyDeviceGateway(DeviceGateway):

    def __init__(
        self,
        rpc_client: Any,
        timeout: float = 10.0,
        http_session: requests.Session | None = None,
    ) -> None:
        self._rpc_client = rpc_client
        self.timeout = timeout
        self._http_session = http_session or requests.Session()
        self._legacy_component_mapper = LegacyComponentMapper()

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
            legacy_device = await self._discover_device_legacy(ip)
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
            legacy_status = await self._get_legacy_device_status(ip)
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
                return await self._execute_legacy_action(
                    ip, component_key, action, parameters or {}
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

    async def _execute_legacy_action(
        self,
        ip: str,
        component_key: str,
        action: str,
        parameters: dict[str, Any],
    ) -> ActionResult:
        action_type = f"{component_key}.{action}"
        part = component_key.split(":")
        component_type = part[0]
        component_id: int | None = None
        if len(part) > 1:
            try:
                component_id = int(part[1])
            except ValueError:
                component_id = None

        command = self._map_legacy_command(component_type, component_id, action)
        if command is None:
            return ActionResult(
                device_ip=ip,
                action_type=action_type,
                success=False,
                message=f"Legacy action {action} not supported for {component_key}",
                error="Unsupported legacy action",
            )

        try:
            response = await self._legacy_get(
                ip, command["endpoint"], command["params"]
            )
            return ActionResult(
                device_ip=ip,
                action_type=action_type,
                success=True,
                message=command["message"],
                data=response,
            )
        except Exception as e:
            return ActionResult(
                device_ip=ip,
                action_type=action_type,
                success=False,
                message=f"Legacy action {action} failed",
                error=str(e),
            )

    def _map_legacy_command(
        self, component_type: str, component_id: int | None, action: str
    ) -> dict[str, Any] | None:
        if component_type == "switch" and component_id is not None:
            endpoint = f"relay/{component_id}"
            relay_actions: dict[str, dict[str, Any]] = {
                "Legacy.Toggle": {
                    "params": {"turn": "toggle"},
                    "message": "Relay toggled successfully",
                },
                "Legacy.TurnOn": {
                    "params": {"turn": "on"},
                    "message": "Relay turned on",
                },
                "Legacy.TurnOff": {
                    "params": {"turn": "off"},
                    "message": "Relay turned off",
                },
            }
            if action in relay_actions:
                return {"endpoint": endpoint, **relay_actions[action]}

        if component_type == "cover" and component_id is not None:
            endpoint = f"roller/{component_id}"
            roller_actions: dict[str, dict[str, Any]] = {
                "Legacy.Open": {
                    "params": {"go": "open"},
                    "message": "Cover opening",
                },
                "Legacy.Close": {
                    "params": {"go": "close"},
                    "message": "Cover closing",
                },
                "Legacy.Stop": {
                    "params": {"go": "stop"},
                    "message": "Cover stopped",
                },
            }
            if action in roller_actions:
                return {"endpoint": endpoint, **roller_actions[action]}

        if component_type == "input" and component_id is not None:
            endpoint = f"settings/relay/{component_id}"
            input_actions: dict[str, dict[str, Any]] = {
                "Legacy.InputMomentary": {
                    "params": {"btn_type": "momentary"},
                    "message": "Input set to momentary",
                },
                "Legacy.InputToggle": {
                    "params": {"btn_type": "toggle"},
                    "message": "Input set to toggle",
                },
                "Legacy.InputEdge": {
                    "params": {"btn_type": "edge"},
                    "message": "Input set to edge",
                },
                "Legacy.InputDetached": {
                    "params": {"btn_type": "detached"},
                    "message": "Input set to detached",
                },
                "Legacy.InputActivation": {
                    "params": {"btn_type": "action"},
                    "message": "Input set to action mode",
                },
                "Legacy.InputMomentaryRelease": {
                    "params": {"btn_type": "momentary_on_release"},
                    "message": "Input set to momentary on release",
                },
                "Legacy.InputReverse": {
                    "params": {"btn_reverse": 1},
                    "message": "Input reversed",
                },
                "Legacy.InputNormal": {
                    "params": {"btn_reverse": 0},
                    "message": "Input polarity reset",
                },
            }
            if action in input_actions:
                return {"endpoint": endpoint, **input_actions[action]}

        return None

    def _get_api_component_type(self, component_type: str) -> str:
        component_type_mapping = {
            "ble": "BLE",
            "wifi": "Wifi",
            "mqtt": "Mqtt",
            "knx": "KNX",
            "ws": "WS",
            "eth": "Eth",
            "http": "HTTP",
            "sys": "Sys",
            "cloud": "Cloud",
            "shelly": "Shelly",
            "schedule": "Schedule",
            "webhook": "Webhook",
            "kvs": "KVS",
            "script": "Script",
            "switch": "Switch",
            "input": "Input",
            "cover": "Cover",
            "light": "Light",
            "rgb": "RGB",
            "rgbw": "RGBW",
            "cct": "CCT",
            "temperature": "Temperature",
            "humidity": "Humidity",
            "voltmeter": "Voltmeter",
            "em": "EM",
            "em1": "EM1",
            "pm1": "PM1",
            "smoke": "Smoke",
            "matter": "Matter",
            "zigbee": "Zigbee",
            "bthome": "BTHome",
            "modbus": "Modbus",
            "dali": "DALI",
            "devicepower": "DevicePower",
            "ui": "UI",
        }

        return component_type_mapping.get(
            component_type.lower(), component_type.title()
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
        component_prefix = self._get_api_component_type(component_type)

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

    async def _discover_device_legacy(self, ip: str) -> DiscoveredDevice | None:
        try:
            start_time = time.perf_counter()
            device_info = await self._fetch_legacy_json(ip, "shelly")
            response_time = time.perf_counter() - start_time

            status_data = await self._fetch_optional_legacy_json(ip, "status")
            settings_data = await self._fetch_optional_legacy_json(ip, "settings")

            device_name = self._derive_legacy_device_name(device_info, settings_data)
            firmware_version = (
                device_info.get("fw_id")
                or device_info.get("fw")
                or device_info.get("fw_ver")
            )

            has_update_flag = self._parse_legacy_update_flag(status_data)
            if has_update_flag is None:
                device_status = Status.DETECTED
                has_update_value = False
            else:
                device_status = (
                    Status.UPDATE_AVAILABLE
                    if has_update_flag
                    else Status.NO_UPDATE_NEEDED
                )
                has_update_value = has_update_flag

            return DiscoveredDevice(
                ip=ip,
                status=device_status,
                device_id=device_info.get("id"),
                device_type=device_info.get("model") or device_info.get("type"),
                device_name=device_name,
                firmware_version=firmware_version,
                response_time=response_time,
                last_seen=datetime.now(),
                has_update=has_update_value,
                status_snapshot=status_data or None,
            )
        except Exception as e:
            logger.debug(
                "Legacy discovery failed for %s: %s",
                ip,
                e,
                exc_info=True,
            )
            return None

    async def _get_legacy_device_status(self, ip: str) -> DeviceStatus | None:
        try:
            device_info = await self._fetch_legacy_json(ip, "shelly")
            status_data = await self._fetch_legacy_json(ip, "status")
            settings_data = await self._fetch_optional_legacy_json(ip, "settings")
        except Exception as e:
            logger.debug(
                "Failed to fetch legacy data for %s: %s",
                ip,
                e,
                exc_info=True,
            )
            return None

        components = self._legacy_component_mapper.map(
            device_info, status_data, settings_data
        )
        legacy_payload = {
            "components": components,
            "cfg_rev": (
                (settings_data or {}).get("cfg_rev", 0)
                if isinstance(settings_data, dict)
                else 0
            ),
            "total": len(components),
            "offset": 0,
        }
        device_info_payload = {
            "name": device_info.get("name"),
            "model": device_info.get("type") or device_info.get("model"),
            "fw_id": device_info.get("fw_id")
            or device_info.get("fw_ver")
            or device_info.get("fw"),
            "mac": device_info.get("mac"),
            "app": device_info.get("type"),
        }

        return DeviceStatus.from_raw_response(
            ip,
            legacy_payload,
            available_methods=[],
            device_info_data=device_info_payload,
            status_data=None,
        )

    async def _fetch_optional_legacy_json(
        self, ip: str, endpoint: str
    ) -> dict[str, Any]:
        try:
            return await self._fetch_legacy_json(ip, endpoint)
        except Exception as e:
            logger.debug(
                "Optional legacy endpoint %s failed for %s: %s",
                endpoint,
                ip,
                e,
            )
            return {}

    async def _fetch_legacy_json(self, ip: str, endpoint: str) -> dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_fetch_legacy_json, ip, endpoint
        )

    def _sync_fetch_legacy_json(self, ip: str, endpoint: str) -> dict[str, Any]:
        url = f"http://{ip}/{endpoint.lstrip('/')}"
        response = self._http_session.get(url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"Legacy endpoint {endpoint} did not return JSON object")
        return cast(dict[str, Any], data)

    async def _legacy_get(
        self, ip: str, endpoint: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._sync_legacy_get, ip, endpoint, params
        )

    def _sync_legacy_get(
        self, ip: str, endpoint: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"http://{ip}/{endpoint.lstrip('/')}"
        response = self._http_session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError(
                    f"Legacy endpoint {endpoint} did not return JSON object"
                )
            return cast(dict[str, Any], data)
        except ValueError:
            return {"response": response.text}

    def _derive_legacy_device_name(
        self,
        device_info: dict[str, Any],
        settings_data: dict[str, Any] | None,
    ) -> str | None:
        settings = settings_data or {}
        name_from_settings = settings.get("name")
        if isinstance(name_from_settings, str) and name_from_settings:
            return name_from_settings

        device_settings = settings.get("device")
        if isinstance(device_settings, dict):
            device_settings_name = device_settings.get("name")
            if isinstance(device_settings_name, str) and device_settings_name:
                return device_settings_name

        device_name = device_info.get("name")
        if isinstance(device_name, str) and device_name:
            return device_name

        device_id = device_info.get("id")
        if isinstance(device_id, str) and device_id:
            return device_id

        return None

    def _parse_legacy_update_flag(
        self, status_data: dict[str, Any] | None
    ) -> bool | None:
        if not isinstance(status_data, dict):
            return None

        has_update = status_data.get("has_update")
        if isinstance(has_update, bool):
            return has_update

        update_block = status_data.get("update")
        if isinstance(update_block, dict):
            update_flag = update_block.get("has_update")
            if isinstance(update_flag, bool):
                return update_flag

            new_version = update_block.get("new_version")
            old_version = update_block.get("old_version")
            if isinstance(new_version, str) and isinstance(old_version, str):
                return new_version != old_version

        return None
