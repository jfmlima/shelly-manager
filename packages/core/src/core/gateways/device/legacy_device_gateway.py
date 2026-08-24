"""
Legacy device gateway for Gen1 Shelly devices.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ...domain.entities.device_status import DeviceStatus
from ...domain.entities.discovered_device import DiscoveredDevice
from ...domain.entities.exceptions import (
    ConfigurationError,
    DeviceAuthenticationError,
)
from ...domain.enums.enums import Status
from ...domain.value_objects.action_result import ActionResult
from ...utils.validation import normalize_mac
from ..network.legacy_http_client import LegacyHttpClient
from .legacy_component_mapper import LegacyComponentMapper

if TYPE_CHECKING:
    from ...services.auth_state_cache import AuthStateCache
    from ...services.authentication_service import AuthenticationService

logger = logging.getLogger(__name__)

# Gen1 exposes MQTT as ``mqtt_*`` params on the device-level ``/settings``, so it
# shares an endpoint with ``sys`` rather than having one of its own.
LEGACY_SETTINGS_ENDPOINTS: dict[str, str] = {
    "sys": "settings",
    "mqtt": "settings",
    "cloud": "settings/cloud",
    "wifi": "settings/sta",
    # Gen1 splits WiFi across three resources behind the single "wifi"
    # component; these synthetic types exist only for the restore path.
    "wifi_sta1": "settings/sta1",
    "wifi_ap": "settings/ap",
}
LEGACY_INDEXED_SETTINGS_ENDPOINTS: dict[str, str] = {
    "switch": "settings/relay",
    "cover": "settings/roller",
    "input": "settings/input",
}


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

    async def _ensure_mac(self, ip: str, timeout: float | None = None) -> str | None:
        """Get MAC address for an IP, fetching from /shelly if not cached."""
        normalized_ip = normalize_mac(ip)
        if normalized_ip in self._ip_to_mac:
            return self._ip_to_mac[normalized_ip]
        try:
            shelly_data = await self._http_client.fetch_json(
                ip, "shelly", timeout=timeout
            )
            mac = shelly_data.get("mac")
            if mac:
                normalized_mac = normalize_mac(mac)
                self._ip_to_mac[normalized_ip] = normalized_mac
                return normalized_mac
        except Exception:
            pass
        return None

    async def _resolve_auth(
        self, ip: str, timeout: float | None = None
    ) -> tuple[str, str] | None:
        """Resolve Basic Auth credentials for a device by IP."""
        if not self._authentication_service:
            return None

        mac = await self._ensure_mac(ip, timeout)
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

    def invalidate_credential_cache(self, mac: str) -> None:
        """Clear cached credentials for a device."""
        normalized_mac = normalize_mac(mac)
        self._basic_auth_cache.pop(normalized_mac, None)

    async def discover_device(
        self, ip: str, timeout: float | None = None
    ) -> DiscoveredDevice | None:
        """Discover a legacy Gen1 Shelly device.

        Args:
            ip: Device IP address
            timeout: Per-request timeout in seconds; falls back to the HTTP
                client default when not provided.

        Returns:
            DiscoveredDevice or None if discovery fails
        """
        try:
            start_time = time.perf_counter()
            device_info = await self._http_client.fetch_json(
                ip, "shelly", timeout=timeout
            )
            response_time = time.perf_counter() - start_time

            # Detect auth requirement from /shelly response
            auth_enabled = device_info.get("auth", False)
            mac = device_info.get("mac")
            auth: tuple[str, str] | None = None

            if auth_enabled and mac and self._auth_state_cache is not None:
                normalized_mac = normalize_mac(mac)
                self._ip_to_mac[normalize_mac(ip)] = normalized_mac
                self._auth_state_cache.mark_auth_required(normalized_mac)
                auth = await self._resolve_auth(ip, timeout)

            # /status and /settings are independent; fetch them concurrently.
            status_data, settings_data = await asyncio.gather(
                self._http_client.fetch_json_optional(
                    ip, "status", auth=auth, timeout=timeout
                ),
                self._http_client.fetch_json_optional(
                    ip, "settings", auth=auth, timeout=timeout
                ),
            )

            device_name = self._derive_device_name(device_info, settings_data)
            firmware_version = (
                device_info.get("fw_id")
                or device_info.get("fw")
                or device_info.get("fw_ver")
            )

            has_update_flag = self._parse_update_flag(status_data)
            update_version = self._parse_update_version(status_data)
            available_version, available_channel = (
                update_version if update_version is not None else (None, None)
            )

            if has_update_flag is None and available_version is None:
                device_status = Status.DETECTED
                has_update_value = False
            else:
                has_update_value = (
                    bool(has_update_flag) or available_version is not None
                )
                device_status = (
                    Status.UPDATE_AVAILABLE
                    if has_update_value
                    else Status.NO_UPDATE_NEEDED
                )

            return DiscoveredDevice(
                ip=ip,
                status=device_status,
                device_id=device_info.get("id"),
                device_type=device_info.get("model") or device_info.get("type"),
                device_name=device_name,
                firmware_version=firmware_version,
                available_firmware_version=available_version,
                available_firmware_channel=available_channel,
                response_time=response_time,
                last_seen=datetime.now(),
                has_update=has_update_value,
                auth_required=auth_enabled,
            )
        except ConfigurationError:
            raise

        except Exception as e:
            logger.debug(
                "Legacy discovery failed for %s: %s",
                ip,
                e,
                exc_info=True,
            )
            return None

    async def get_device_status(
        self, ip: str, timeout: float | None = None
    ) -> DeviceStatus | None:
        """Get device status for a legacy Gen1 device.

        Args:
            ip: Device IP address
            timeout: Per-request timeout in seconds; falls back to the HTTP
                client default when not provided.

        Returns:
            DeviceStatus or None if retrieval fails
        """
        try:
            device_info = await self._http_client.fetch_json(
                ip, "shelly", timeout=timeout
            )

            auth: tuple[str, str] | None = None
            if device_info.get("auth", False):
                mac = device_info.get("mac")
                if mac:
                    normalized_mac = normalize_mac(mac)
                    self._ip_to_mac[normalize_mac(ip)] = normalized_mac
                auth = await self._resolve_auth(ip, timeout)

            status_data = await self._http_client.fetch_json(
                ip, "status", auth=auth, timeout=timeout
            )
            settings_data = await self._http_client.fetch_json_optional(
                ip, "settings", auth=auth, timeout=timeout
            )
        except DeviceAuthenticationError:
            raise
        except ConfigurationError:
            raise
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
            # The legacy HTTP path is, by definition, a Gen1 device.
            "gen": 1,
        }

        return DeviceStatus.from_raw_response(
            ip,
            legacy_payload,
            available_methods=[],
            device_info_data=device_info_payload,
            status_data=None,
        )

    async def fetch_settings(
        self, ip: str, timeout: float | None = None
    ) -> dict[str, Any] | None:
        """Fetch the raw Gen1 ``/settings`` payload for backup capture.

        Returns ``None`` on any failure, including an empty payload, so the
        export stays non-fatal when a device drops mid-capture.
        """
        auth = await self._resolve_auth(ip, timeout)
        settings = await self._http_client.fetch_json_optional(
            ip, "settings", auth=auth, timeout=timeout
        )
        return settings or None

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
            parameters: Action parameters. Only ``Legacy.SetConfig`` reads them;
                the fixed-command actions carry their own params.

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

        command = self._map_legacy_command(
            component_type, component_id, action, parameters
        )
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
        except ConfigurationError:
            raise

        except Exception as e:
            return ActionResult(
                device_ip=ip,
                action_type=action_type,
                success=False,
                message=f"Legacy action {action} failed",
                error=str(e),
            )

    def _map_legacy_command(
        self,
        component_type: str,
        component_id: int | None,
        action: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Map legacy action to HTTP endpoint and parameters."""
        if action == "Legacy.SetConfig":
            return self._map_set_config(component_type, component_id, parameters)

        if action == "Legacy.Reboot" and component_type == "sys":
            return {
                "endpoint": "reboot",
                "params": {},
                "message": "Device reboot requested",
            }

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

    def _map_set_config(
        self,
        component_type: str,
        component_id: int | None,
        parameters: dict[str, Any],
    ) -> dict[str, Any] | None:
        endpoint = LEGACY_SETTINGS_ENDPOINTS.get(component_type)
        if endpoint is None:
            indexed = LEGACY_INDEXED_SETTINGS_ENDPOINTS.get(component_type)
            if indexed is None or component_id is None:
                return None
            endpoint = f"{indexed}/{component_id}"

        return {
            "endpoint": endpoint,
            "params": self._serialize_params(parameters),
            "message": "Configuration applied",
        }

    @staticmethod
    def _serialize_params(parameters: dict[str, Any]) -> dict[str, Any]:
        """Render params as Gen1 query values.

        An empty list serializes to "", which is how Gen1 clears a list field,
        whereas ``None`` is dropped so the field is left untouched instead.
        """
        params: dict[str, Any] = {}
        for name, value in parameters.items():
            if value is None:
                continue
            if isinstance(value, bool):
                params[name] = "true" if value else "false"
            elif isinstance(value, list | tuple):
                params[name] = ",".join(str(item) for item in value)
            else:
                params[name] = value
        return params

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

    def _parse_update_version(
        self, status_data: dict[str, Any] | None
    ) -> tuple[str, str] | None:
        """Parse the version and channel of an available update, if any.

        Stable takes priority over beta, mirroring the RPC (Gen2+) gateway.
        Returns ``None`` when no version-bearing update is reported (the
        boolean-only ``has_update``/``update.has_update`` shorthand some
        Gen1 firmwares report carries no version and isn't captured here).
        """
        if not isinstance(status_data, dict):
            return None

        update_block = status_data.get("update")
        if not isinstance(update_block, dict):
            return None

        new_version = update_block.get("new_version")
        old_version = update_block.get("old_version")
        has_stable = bool(update_block.get("has_update")) or (
            isinstance(new_version, str)
            and isinstance(old_version, str)
            and new_version != old_version
        )
        if has_stable and isinstance(new_version, str) and new_version:
            return new_version, "stable"

        beta_version = update_block.get("beta_version")
        if isinstance(beta_version, str) and beta_version:
            return beta_version, "beta"

        return None
