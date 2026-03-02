"""
Legacy device gateway for Gen1 Shelly devices.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

import requests

from ...domain.entities.device_status import DeviceStatus
from ...domain.entities.discovered_device import DiscoveredDevice
from ...domain.entities.exceptions import DeviceAuthenticationError
from ...domain.enums.enums import Status
from ...domain.value_objects.action_result import ActionResult
from ...utils.validation import normalize_mac
from ..network.legacy_http_client import LegacyHttpClient
from .legacy_component_mapper import LegacyComponentMapper

if TYPE_CHECKING:
    from ...services.auth_state_cache import AuthStateCache
    from ...services.authentication_service import AuthenticationService

logger = logging.getLogger(__name__)


class LegacyDeviceGateway:
    """Adapter for legacy Gen1 Shelly devices using HTTP API."""

    def __init__(
        self,
        http_client: LegacyHttpClient,
        component_mapper: LegacyComponentMapper,
        authentication_service: AuthenticationService | None = None,
        auth_state_cache: AuthStateCache | None = None,
    ) -> None:
        self._http_client = http_client
        self._component_mapper = component_mapper
        self._authentication_service = authentication_service
        self._auth_state_cache = auth_state_cache
        self._ip_to_mac: dict[str, str] = {}
        self._basic_auth_cache: dict[str, tuple[str, str]] = {}

    async def _ensure_mac(self, ip: str) -> str | None:
        """Get MAC address for an IP, fetching from /shelly if not cached."""
        normalized_ip = normalize_mac(ip)
        if normalized_ip in self._ip_to_mac:
            return self._ip_to_mac[normalized_ip]
        try:
            shelly_data = await self._http_client.fetch_json(ip, "shelly")
            mac = shelly_data.get("mac")
            if mac:
                normalized_mac = normalize_mac(mac)
                self._ip_to_mac[normalized_ip] = normalized_mac
                return normalized_mac
        except Exception:
            pass
        return None

    async def _resolve_auth(self, ip: str) -> tuple[str, str] | None:
        """Resolve Basic Auth credentials for a device by IP."""
        if not self._authentication_service:
            return None

        mac = await self._ensure_mac(ip)
        if not mac:
            return None

        if mac in self._basic_auth_cache:
            return self._basic_auth_cache[mac]

        credential = await self._authentication_service.resolve_credentials(mac)
        if credential:
            auth_tuple = (credential.username, credential.password)
            self._basic_auth_cache[mac] = auth_tuple
            return auth_tuple
        return None

    async def _fetch_with_auth(self, ip: str, endpoint: str) -> dict[str, Any]:
        """Fetch JSON with automatic 401 retry using stored credentials."""
        try:
            return await self._http_client.fetch_json(ip, endpoint)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                auth = await self._resolve_auth(ip)
                if auth:
                    return await self._http_client.fetch_json(ip, endpoint, auth=auth)
                raise DeviceAuthenticationError(ip, "No credentials available") from e
            raise

    def invalidate_credential_cache(self, mac: str) -> None:
        """Clear cached credentials for a device."""
        normalized_mac = normalize_mac(mac)
        self._basic_auth_cache.pop(normalized_mac, None)

    async def discover_device(self, ip: str) -> DiscoveredDevice | None:
        """Discover a legacy Gen1 Shelly device.

        Args:
            ip: Device IP address

        Returns:
            DiscoveredDevice or None if discovery fails
        """
        try:
            start_time = time.perf_counter()
            device_info = await self._http_client.fetch_json(ip, "shelly")
            response_time = time.perf_counter() - start_time

            # Detect auth requirement from /shelly response
            auth_enabled = device_info.get("auth", False)
            mac = device_info.get("mac")
            auth: tuple[str, str] | None = None

            if auth_enabled and mac and self._auth_state_cache:
                normalized_mac = normalize_mac(mac)
                self._ip_to_mac[normalize_mac(ip)] = normalized_mac
                self._auth_state_cache.mark_auth_required(normalized_mac)
                auth = await self._resolve_auth(ip)

            status_data = await self._http_client.fetch_json_optional(
                ip, "status", auth=auth
            )
            settings_data = await self._http_client.fetch_json_optional(
                ip, "settings", auth=auth
            )

            device_name = self._derive_device_name(device_info, settings_data)
            firmware_version = (
                device_info.get("fw_id")
                or device_info.get("fw")
                or device_info.get("fw_ver")
            )

            has_update_flag = self._parse_update_flag(status_data)
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
                auth_required=auth_enabled,
            )
        except Exception as e:
            logger.debug(
                "Legacy discovery failed for %s: %s",
                ip,
                e,
                exc_info=True,
            )
            return None

    async def get_device_status(self, ip: str) -> DeviceStatus | None:
        """Get device status for a legacy Gen1 device.

        Args:
            ip: Device IP address

        Returns:
            DeviceStatus or None if retrieval fails
        """
        try:
            device_info = await self._http_client.fetch_json(ip, "shelly")
            status_data = await self._fetch_with_auth(ip, "status")
            auth = (
                await self._resolve_auth(ip) if self._authentication_service else None
            )
            settings_data = await self._http_client.fetch_json_optional(
                ip, "settings", auth=auth
            )
        except DeviceAuthenticationError:
            logger.warning("Authentication failed for Gen1 device %s", ip)
            return None
        except Exception as e:
            logger.debug(
                "Failed to fetch legacy data for %s: %s",
                ip,
                e,
                exc_info=True,
            )
            return None

        components = self._component_mapper.map(device_info, status_data, settings_data)
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

    async def execute_action(
        self,
        ip: str,
        component_key: str,
        action: str,
        parameters: dict[str, Any],
    ) -> ActionResult:
        """Execute a legacy action on a Gen1 device.

        Args:
            ip: Device IP address
            component_key: Component key (e.g., 'switch:0', 'input:1')
            action: Action name (must start with 'Legacy.')
            parameters: Action parameters (unused for legacy actions)

        Returns:
            ActionResult with execution status
        """
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
            auth = (
                await self._resolve_auth(ip) if self._authentication_service else None
            )
            response = await self._http_client.get_with_params(
                ip, command["endpoint"], command["params"], auth=auth
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
        """Map legacy action to HTTP endpoint and parameters."""
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

    def _derive_device_name(
        self,
        device_info: dict[str, Any],
        settings_data: dict[str, Any] | None,
    ) -> str | None:
        """Derive device name from various sources."""
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

    def _parse_update_flag(self, status_data: dict[str, Any] | None) -> bool | None:
        """Parse update availability flag from status data."""
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
