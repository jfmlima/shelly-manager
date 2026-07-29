"""Translate a raw Gen1 ``/settings`` snapshot into settable request params.

Gen1 devices have no RPC: a restore replays the raw ``/settings`` payload
captured at backup time against the per-resource setter endpoints. This module
owns the wire knowledge that translation needs: which captured params are
documented as settable (so read-only echoes are never sent back), which section
of ``/settings`` holds each component type, and the fields whose setter accepts
a different name than the one GET echoes.

Pure dict-in/dict-out: no I/O, independently testable against the documented
Gen1 API (https://shelly-api-docs.shelly.cloud/gen1/).
"""

from typing import Any

# Section of the raw /settings holding each component's config. "" is the top level.
# wifi_sta1/wifi_ap are synthetic types for the extra Gen1 WiFi resources replayed
# behind the single "wifi" component (see wifi_subresources).
GEN1_SECTION_BY_TYPE: dict[str, str] = {
    "switch": "relays",
    "cover": "rollers",
    "input": "inputs",
    "sys": "",
    "mqtt": "mqtt",
    "cloud": "cloud",
    "wifi": "wifi_sta",
    "wifi_sta1": "wifi_sta1",
    "wifi_ap": "wifi_ap",
}

# Restorable Gen1 settings per component type, as GET /settings names them. Only
# params documented as settable at https://shelly-api-docs.shelly.cloud/gen1/ are
# listed, so read-only echoes (ison, has_timer, is_valid, safety_switch) are
# never sent back. Fields a model does not have are absent and skip themselves,
# which is what lets one table serve every Gen1 model.
GEN1_RESTORABLE_BY_TYPE: dict[str, tuple[str, ...]] = {
    "switch": (
        "name",
        "appliance_type",
        "default_state",
        "btn_type",
        "btn_reverse",
        # Shelly 1L exposes two inputs instead of one.
        "btn1_type",
        "btn1_reverse",
        "btn2_type",
        "btn2_reverse",
        "swap_inputs",
        "auto_on",
        "auto_off",
        "schedule",
        "schedule_rules",
        "max_power",
        # On Shelly 1/1L "power" is the settable user power constant shown in
        # meters, not a live reading (live power is echoed under "meters").
        "power",
    ),
    "cover": (
        "default_state",
        "input_mode",
        "button_type",
        "btn_reverse",
        "swap",
        "swap_inputs",
        "maxtime",
        "maxtime_open",
        "maxtime_close",
        "positioning",
        "obstacle_mode",
        "obstacle_action",
        "obstacle_power",
        "obstacle_delay",
        "ends_delay",
        "off_power",
        "safety_mode",
        "safety_action",
        "safety_allowed_on_trigger",
        "schedule",
        "schedule_rules",
    ),
    # "mode" is deliberately absent: Gen1 applies it with a reboot, so it is
    # replayed alone as a pre-phase (the restore's mode sync), never in this
    # batch.
    "sys": (
        "name",
        "timezone",
        "tzautodetect",
        "tz_utc_offset",
        "tz_dst",
        "tz_dst_auto",
        "lat",
        "lng",
        "discoverable",
        "led_status_disable",
        "led_power_disable",
        "sntp.server",
        # Device-level overpower threshold (1PM, Plug/PlugS, 2.5 in roller
        # mode); distinct from the per-relay max_power.
        "max_power",
        "longpush_time",
        "factory_reset_from_switch",
        "wifirecovery_reboot_enabled",
        "debug_enable",
        "allow_cross_origin",
        "supply_voltage",
        "power_correction",
        # 2.5 roller favourite positions live on /settings/favorites/{i} (not
        # replayed); only their enable flag is a plain /settings param.
        "favorites_enabled",
        "coiot.enabled",
        "coiot.update_period",
        "coiot.peer",
        "ap_roaming.enabled",
        "ap_roaming.threshold",
        "longpush_duration_ms.min",
        "longpush_duration_ms.max",
        "multipush_time_between_pushes_ms.max",
    ),
    # Only i3/Button1 expose /settings/input/{i}. Relay-bearing models never
    # echo an "inputs" section in /settings (their input config lives on the
    # owning relay), so their inputs skip as having nothing captured.
    "input": ("name", "btn_type", "btn_reverse"),
    # mqtt_pass is not echoed by GET /settings, so it cannot be restored.
    "mqtt": (
        "enable",
        "server",
        "user",
        "id",
        "clean_session",
        "retain",
        "keep_alive",
        "update_period",
        "max_qos",
        "reconnect_timeout_min",
        "reconnect_timeout_max",
    ),
    "cloud": ("enabled",),
    # The WiFi STA "key" is not echoed by GET /settings, so it cannot be restored.
    "wifi": ("enabled", "ssid", "ipv4_method", "ip", "gw", "mask", "dns"),
    # The AP SSID is device-fixed and not settable; the AP key, unlike the STA
    # one, IS echoed by GET /settings and round-trips.
    "wifi_ap": ("enabled", "key"),
}
# /settings/sta1 (fallback STA) is documented as an identical resource to
# /settings/sta.
GEN1_RESTORABLE_BY_TYPE["wifi_sta1"] = GEN1_RESTORABLE_BY_TYPE["wifi"]

# GET /settings echoes several fields under a different name than the one their
# setter accepts; sending the echoed name is silently ignored by the device.
GEN1_PARAM_RENAMES: dict[str, dict[str, str]] = {
    "cover": {"button_type": "btn_type"},
    "sys": {
        "sntp.server": "sntp_server",
        "coiot.enabled": "coiot_enable",
        "coiot.update_period": "coiot_update_period",
        "coiot.peer": "coiot_peer",
        "ap_roaming.enabled": "ap_roaming_enabled",
        "ap_roaming.threshold": "ap_roaming_threshold",
        "longpush_duration_ms.min": "longpush_duration_ms_min",
        "longpush_duration_ms.max": "longpush_duration_ms_max",
        "multipush_time_between_pushes_ms.max": (
            "multipush_time_between_pushes_ms_max"
        ),
    },
    "mqtt": {name: f"mqtt_{name}" for name in GEN1_RESTORABLE_BY_TYPE["mqtt"]},
    "wifi": {"gw": "gateway", "mask": "netmask"},
}
GEN1_PARAM_RENAMES["wifi_sta1"] = GEN1_PARAM_RENAMES["wifi"]

# Gen1 splits WiFi across /settings/sta, /settings/sta1 (fallback STA) and
# /settings/ap; all three replay behind the single "wifi" component. The AP is
# last: enabling one mode disables the other on the device, so the resource
# enabled in the backup must win.
WIFI_SUBTYPES: tuple[str, ...] = ("wifi", "wifi_sta1", "wifi_ap")


def restorable_params(
    key: str, ctype: str | None, settings: dict[str, Any]
) -> dict[str, Any] | None:
    """The settable params captured for one component, under their setter names.

    ``None`` when the type has no Gen1 settings endpoint at all; ``{}`` when it
    has one but the snapshot holds nothing to send (e.g. inputs on relay-bearing
    models, which never echo an ``inputs`` settings section).
    """
    allowed = GEN1_RESTORABLE_BY_TYPE.get(ctype or "")
    if allowed is None:
        return None

    section = _section(key, ctype or "", settings)
    if section is None:
        return {}

    renames = GEN1_PARAM_RENAMES.get(ctype or "", {})
    params: dict[str, Any] = {}
    for attr in allowed:
        value = _dig(section, attr)
        if value is not None:
            params[renames.get(attr, attr)] = value
    return params


def wifi_subresources(settings: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """The captured WiFi resources to replay, in apply order (AP last).

    Each item is ``(subtype, params)``; resources the snapshot holds nothing
    for are omitted.
    """
    subresources: list[tuple[str, dict[str, Any]]] = []
    for subtype in WIFI_SUBTYPES:
        params = restorable_params(subtype, subtype, settings)
        if params:
            subresources.append((subtype, params))
    return subresources


def _section(key: str, ctype: str, settings: dict[str, Any]) -> dict[str, Any] | None:
    section_name = GEN1_SECTION_BY_TYPE[ctype]
    section: Any = settings if not section_name else settings.get(section_name)

    # relays/rollers are arrays parallel to the component id.
    if isinstance(section, list):
        try:
            index = int(key.split(":")[1])
        except (IndexError, ValueError):
            return None
        section = section[index] if 0 <= index < len(section) else None

    return section if isinstance(section, dict) else None


def _dig(section: dict[str, Any], path: str) -> Any:
    value: Any = section
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value
