"""
Helpers for translating legacy Shelly Gen1 payloads into modern component structures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

LEGACY_SWITCH_ACTIONS = ["Legacy.Toggle", "Legacy.TurnOn", "Legacy.TurnOff"]
LEGACY_COVER_ACTIONS = ["Legacy.Open", "Legacy.Close", "Legacy.Stop"]
LEGACY_INPUT_ACTIONS = [
    "Legacy.InputMomentary",
    "Legacy.InputToggle",
    "Legacy.InputEdge",
    "Legacy.InputDetached",
    "Legacy.InputActivation",
    "Legacy.InputMomentaryRelease",
    "Legacy.InputReverse",
    "Legacy.InputNormal",
]


class LegacyComponentMapper:
    """Translate Gen1 payloads into component dictionaries consumed by ComponentFactory."""

    def map(
        self,
        device_info: dict[str, Any],
        status_data: dict[str, Any],
        settings_data: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        status = status_data if isinstance(status_data, dict) else {}
        settings = settings_data if isinstance(settings_data, dict) else {}
        timezone = settings.get("timezone") or settings.get("tz")

        components: list[dict[str, Any]] = []
        components.append(
            self._build_system_component(device_info, status, settings, timezone)
        )

        wifi_component = self._build_wifi_component(status, settings)
        if wifi_component:
            components.append(wifi_component)

        cloud_component = self._build_cloud_component(status, settings)
        if cloud_component:
            components.append(cloud_component)

        mqtt_component = self._build_mqtt_component(status, settings)
        if mqtt_component:
            components.append(mqtt_component)

        components.extend(self._build_input_components(status, settings))
        components.extend(self._build_switch_components(status, settings))
        components.extend(self._build_cover_components(status, settings))

        return components

    def _build_system_component(
        self,
        device_info: dict[str, Any],
        status: dict[str, Any],
        settings: dict[str, Any],
        timezone: str | None,
    ) -> dict[str, Any]:
        device_settings = settings.get("device", {})
        return {
            "key": "sys",
            "status": {
                "mac": device_info.get("mac") or device_settings.get("mac"),
                "uptime": status.get("uptime", 0),
                "restart_required": False,
                "ram_size": status.get("ram_total") or status.get("ram_size") or 0,
                "ram_free": status.get("ram_free", 0),
                "fs_size": status.get("fs_total") or status.get("fs_size") or 0,
                "fs_free": status.get("fs_free", 0),
                "available_updates": self._build_legacy_update_info(status),
                "unixtime": status.get("unixtime", int(datetime.now().timestamp())),
            },
            "config": {
                "device": {
                    "name": device_info.get("name") or settings.get("name"),
                    "fw_id": device_info.get("fw_id")
                    or device_info.get("fw_ver")
                    or device_info.get("fw"),
                },
                "location": {"tz": timezone},
            },
            "attrs": {},
        }

    def _build_wifi_component(
        self, status: dict[str, Any], settings: dict[str, Any]
    ) -> dict[str, Any] | None:
        wifi_status = status.get("wifi_sta")
        if not isinstance(wifi_status, dict):
            return None

        return {
            "key": "wifi",
            "status": {
                "sta_ip": wifi_status.get("ip"),
                "sta_ip6": wifi_status.get("ipv6", []),
                "status": "got ip" if wifi_status.get("connected") else "disconnected",
                "ssid": wifi_status.get("ssid"),
                "bssid": wifi_status.get("bssid"),
                "rssi": wifi_status.get("rssi", wifi_status.get("signal", 0)),
            },
            "config": settings.get("wifi_sta") or {},
            "attrs": {},
        }

    def _build_cloud_component(
        self, status: dict[str, Any], settings: dict[str, Any]
    ) -> dict[str, Any] | None:
        cloud_status = status.get("cloud")
        if not isinstance(cloud_status, dict) and not settings.get("cloud"):
            return None

        cloud_cfg = settings.get("cloud") or {}
        return {
            "key": "cloud",
            "status": {
                "connected": (cloud_status or {}).get("connected", False),
            },
            "config": {
                "enable": cloud_cfg.get(
                    "enable", (cloud_status or {}).get("enabled", False)
                ),
                "server": cloud_cfg.get("server"),
            },
            "attrs": {},
        }

    def _build_mqtt_component(
        self, status: dict[str, Any], settings: dict[str, Any]
    ) -> dict[str, Any] | None:
        mqtt_status = status.get("mqtt")
        if not isinstance(mqtt_status, dict) and not settings.get("mqtt"):
            return None

        mqtt_cfg = settings.get("mqtt") or {}
        return {
            "key": "mqtt",
            "status": {
                "connected": (mqtt_status or {}).get("connected", False),
            },
            "config": {
                "enable": mqtt_cfg.get("enable", mqtt_cfg.get("enable_control", False)),
                "server": mqtt_cfg.get("server"),
                "client_id": mqtt_cfg.get("client_id"),
                "user": mqtt_cfg.get("user"),
                "topic_prefix": mqtt_cfg.get("topic"),
                "rpc_ntf": mqtt_cfg.get("rpc_ntf", False),
                "status_ntf": mqtt_cfg.get("status_ntf", False),
                "use_client_cert": mqtt_cfg.get("use_client_cert", False),
                "enable_rpc": mqtt_cfg.get("enable_rpc", False),
                "enable_control": mqtt_cfg.get("enable_control", False),
            },
            "attrs": {},
        }

    def _build_input_components(
        self, status: dict[str, Any], settings: dict[str, Any]
    ) -> list[dict[str, Any]]:
        components: list[dict[str, Any]] = []

        inputs_block = status.get("inputs")
        if not isinstance(inputs_block, list):
            inputs_block = status.get("input")
        inputs = inputs_block if isinstance(inputs_block, list) else []
        input_configs = settings.get("inputs") or settings.get("input") or []
        for idx, input_status in enumerate(inputs):
            if not isinstance(input_status, dict):
                continue
            config = (
                input_configs[idx]
                if idx < len(input_configs) and isinstance(input_configs[idx], dict)
                else {}
            )
            components.append(
                {
                    "key": f"input:{idx}",
                    "status": {
                        "state": bool(input_status.get("input")),
                    },
                    "config": {
                        "name": config.get("name"),
                        "type": config.get("type", "switch"),
                        "enable": config.get("enable", True),
                        "invert": config.get("invert", False),
                    },
                    "attrs": {
                        "legacy_component": "input",
                        "legacy_id": idx,
                        "legacy_actions": LEGACY_INPUT_ACTIONS.copy(),
                    },
                }
            )
        return components

    def _build_switch_components(
        self, status: dict[str, Any], settings: dict[str, Any]
    ) -> list[dict[str, Any]]:
        components: list[dict[str, Any]] = []
        relays = status.get("relays", [])
        meters = status.get("meters", [])
        relay_configs = settings.get("relays") or []
        if not isinstance(relays, list):
            return components

        for idx, relay in enumerate(relays):
            if not isinstance(relay, dict):
                continue
            meter = (
                meters[idx]
                if idx < len(meters) and isinstance(meters[idx], dict)
                else {}
            )
            config = (
                relay_configs[idx]
                if idx < len(relay_configs) and isinstance(relay_configs[idx], dict)
                else {}
            )
            components.append(
                {
                    "key": f"switch:{idx}",
                    "status": {
                        "output": relay.get("ison"),
                        "apower": meter.get("power", relay.get("power", 0.0)),
                        "voltage": meter.get("voltage", status.get("voltage", 0.0)),
                        "current": meter.get("current", 0.0),
                        "freq": meter.get("freq", status.get("freq", 0.0)),
                        "temperature": self._format_temperature(relay, status),
                        "aenergy": {
                            "total": meter.get("total", 0.0),
                        },
                        "pf": meter.get("pf", 0.0),
                        "source": relay.get("source", "unknown"),
                    },
                    "config": {
                        "name": config.get("name"),
                        "auto_on": config.get("auto_on", False),
                        "auto_off": config.get("auto_off", False),
                        "power_limit": config.get(
                            "power_limit", config.get("max_power", 0.0)
                        ),
                        "current_limit": config.get(
                            "current_limit", config.get("max_current", 0.0)
                        ),
                    },
                    "attrs": {
                        "legacy_component": "relay",
                        "legacy_id": idx,
                        "legacy_actions": LEGACY_SWITCH_ACTIONS.copy(),
                    },
                }
            )
        return components

    def _build_cover_components(
        self, status: dict[str, Any], settings: dict[str, Any]
    ) -> list[dict[str, Any]]:
        components: list[dict[str, Any]] = []
        rollers = status.get("rollers", [])
        roller_configs = settings.get("rollers") or []
        if not isinstance(rollers, list):
            return components

        for idx, roller in enumerate(rollers):
            if not isinstance(roller, dict):
                continue
            config = (
                roller_configs[idx]
                if idx < len(roller_configs) and isinstance(roller_configs[idx], dict)
                else {}
            )
            components.append(
                {
                    "key": f"cover:{idx}",
                    "status": {
                        "state": roller.get("state"),
                        "current_pos": roller.get("pos"),
                        "apower": roller.get("power", 0.0),
                        "voltage": status.get("voltage", 0.0),
                        "temperature": self._format_temperature(roller, status),
                        "last_direction": roller.get("last_direction", ""),
                    },
                    "config": {
                        "name": config.get("name"),
                        "maxtime_open": config.get("maxtime_open", 0),
                        "maxtime_close": config.get("maxtime_close", 0),
                        "power_limit": config.get("power_limit", 0),
                    },
                    "attrs": {
                        "legacy_component": "roller",
                        "legacy_id": idx,
                        "legacy_actions": LEGACY_COVER_ACTIONS.copy(),
                    },
                }
            )

        return components

    def _format_temperature(
        self, relay_status: dict[str, Any], status: dict[str, Any]
    ) -> dict[str, float] | None:
        temperature = relay_status.get("temperature")
        if isinstance(temperature, int | float):
            temp_c = float(temperature)
            return {"tC": temp_c, "tF": temp_c * 9 / 5 + 32}

        tmp = status.get("tmp")
        if isinstance(tmp, dict) and isinstance(tmp.get("tC"), int | float):
            temp_c = float(tmp.get("tC"))
            temp_f = float(tmp.get("tF", temp_c * 9 / 5 + 32))
            return {"tC": temp_c, "tF": temp_f}

        if isinstance(status.get("temperature"), int | float):
            temp_c = float(status.get("temperature"))
            return {"tC": temp_c, "tF": temp_c * 9 / 5 + 32}

        return None

    def _build_legacy_update_info(
        self, status_data: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        if not isinstance(status_data, dict):
            return {}

        update_block = status_data.get("update")
        if not isinstance(update_block, dict):
            return {}

        entries: dict[str, dict[str, Any]] = {}

        new_version = update_block.get("new_version")
        old_version = update_block.get("old_version")
        if (
            isinstance(new_version, str)
            and new_version
            and isinstance(old_version, str)
            and new_version != old_version
        ) or update_block.get("has_update"):
            entries["stable"] = {
                "version": new_version,
                "build_id": update_block.get("build_id"),
                "name": update_block.get("status"),
                "desc": update_block.get("status"),
            }

        beta_version = update_block.get("beta_version")
        if isinstance(beta_version, str) and beta_version:
            entries["beta"] = {
                "version": beta_version,
                "build_id": update_block.get("build_id"),
                "name": "beta",
                "desc": update_block.get("status"),
            }

        return {k: v for k, v in entries.items() if v.get("version")}
