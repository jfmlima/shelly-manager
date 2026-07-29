"""Wire-param pins for the Gen1 /settings translation.

These tests pin the literal params a Gen1 restore sends per component, so any
change to the settable-param tables, renames, or section layout shows up as a
failing pin rather than a silent wire change.
"""

from core.domain.services.gen1_settings_translation import (
    restorable_params,
    wifi_subresources,
)


def _gen1_settings():
    """A raw Gen1 /settings payload, shaped as the device echoes it.

    Field names follow https://shelly-api-docs.shelly.cloud/gen1/; note the
    read-only echoes (relay ison/has_timer, roller state/power) and the fields
    GET names differently from their setter (wifi gw/mask, roller button_type,
    nested sntp.server/coiot/ap_roaming). Deliberately cross-model: relay power
    (Shelly 1), rollers/favorites (2.5), inputs (i3), led_power_disable (PlugS).
    """
    return {
        "device": {"type": "SHSW-1", "mac": "AABBCCDDEEFF"},
        "fw": "20230913-112003/v1.14.0",
        "name": "Hallway",
        "mode": "relay",
        "timezone": "Europe/Lisbon",
        "tzautodetect": False,
        "tz_utc_offset": 3600,
        "tz_dst": False,
        "tz_dst_auto": True,
        "lat": 38.7223,
        "lng": -9.1393,
        "discoverable": True,
        "led_status_disable": False,
        "led_power_disable": False,
        "max_power": 3500,
        "longpush_time": 1000,
        "factory_reset_from_switch": True,
        "wifirecovery_reboot_enabled": True,
        "debug_enable": False,
        "allow_cross_origin": False,
        "supply_voltage": 0,
        "power_correction": 1,
        "favorites_enabled": True,
        "coiot": {"enabled": True, "update_period": 15, "peer": "10.0.0.2:5683"},
        "ap_roaming": {"enabled": True, "threshold": -70},
        "longpush_duration_ms": {"min": 800, "max": 3000},
        "multipush_time_between_pushes_ms": {"max": 500},
        "sntp": {"server": "pool.ntp.org", "enabled": True},
        "login": {"enabled": True, "username": "admin"},
        "inputs": [{"name": "Left button", "btn_type": "momentary", "btn_reverse": 0}],
        "relays": [
            {
                "name": "Hallway light",
                "appliance_type": "General",
                "ison": True,
                "has_timer": False,
                "power": 12.5,
                "default_state": "last",
                "btn_type": "momentary",
                "btn_reverse": 0,
                "auto_on": 0,
                "auto_off": 30.5,
                "schedule": True,
                "schedule_rules": ["0700-012345-on", "2200-012345-off"],
                "max_power": 0,
            }
        ],
        "rollers": [
            {
                "maxtime": 20,
                "maxtime_open": 25,
                "maxtime_close": 24,
                "default_state": "stop",
                "swap": False,
                "input_mode": "openclose",
                "button_type": "toggle",
                "btn_reverse": 0,
                "state": "stop",
                "power": 0,
                "is_valid": True,
                "safety_switch": False,
                "positioning": True,
                "schedule_rules": [],
            }
        ],
        "wifi_sta": {
            "enabled": True,
            "ssid": "Castle",
            "ipv4_method": "static",
            "ip": "192.168.1.100",
            "gw": "192.168.1.1",
            "mask": "255.255.255.0",
            "dns": "8.8.8.8",
        },
        "wifi_sta1": {
            "enabled": False,
            "ssid": "CastleFallback",
            "ipv4_method": "dhcp",
            "ip": None,
            "gw": None,
            "mask": None,
            "dns": None,
        },
        "wifi_ap": {"enabled": False, "ssid": "shelly1-DDEEFF", "key": "appass"},
        "mqtt": {
            "enable": True,
            "server": "10.0.0.1:1883",
            "user": "shelly",
            "id": "shelly1-DDEEFF",
            "clean_session": True,
            "retain": False,
            "keep_alive": 60,
            "max_qos": 0,
            "update_period": 30,
            "reconnect_timeout_min": 2.0,
            "reconnect_timeout_max": 60.0,
        },
        "cloud": {"enabled": True, "connected": True},
    }


class TestRestorableParams:
    def test_it_extracts_the_documented_relay_settings(self):
        # Exactly the documented settable params of /settings/relay/{index}.
        assert restorable_params("switch:0", "switch", _gen1_settings()) == {
            "name": "Hallway light",
            "appliance_type": "General",
            "default_state": "last",
            "btn_type": "momentary",
            "btn_reverse": 0,
            "auto_on": 0,
            "auto_off": 30.5,
            "schedule": True,
            "schedule_rules": ["0700-012345-on", "2200-012345-off"],
            "max_power": 0,
            # The Shelly 1/1L user power constant: settable, unlike the live
            # readings under "meters".
            "power": 12.5,
        }

    def test_it_drops_readonly_relay_fields(self):
        params = restorable_params("switch:0", "switch", _gen1_settings())

        # Echoed by GET /settings but rejected/meaningless as settings.
        for read_only in ("ison", "has_timer"):
            assert read_only not in params

    def test_it_renames_wifi_fields_to_their_setter_names(self):
        # GET /settings echoes gw/mask; /settings/sta only accepts gateway/netmask.
        assert restorable_params("wifi", "wifi", _gen1_settings()) == {
            "enabled": True,
            "ssid": "Castle",
            "ipv4_method": "static",
            "ip": "192.168.1.100",
            "gateway": "192.168.1.1",
            "netmask": "255.255.255.0",
            "dns": "8.8.8.8",
        }

    def test_it_renames_the_roller_button_type_to_its_setter_name(self):
        params = restorable_params("cover:0", "cover", _gen1_settings())

        # GET /settings echoes button_type; /settings/roller/{i} accepts btn_type.
        assert params["btn_type"] == "toggle"
        assert "button_type" not in params
        assert params["maxtime_open"] == 25
        assert params["schedule_rules"] == []
        for read_only in ("state", "power", "is_valid", "safety_switch"):
            assert read_only not in params

    def test_it_flattens_the_nested_sntp_server_for_sys(self):
        # Nested echoes (sntp.server, coiot.*, ap_roaming.*, the i3 timing
        # blocks) flatten to the names their setters accept.
        assert restorable_params("sys", "sys", _gen1_settings()) == {
            "name": "Hallway",
            "timezone": "Europe/Lisbon",
            "tzautodetect": False,
            "tz_utc_offset": 3600,
            "tz_dst": False,
            "tz_dst_auto": True,
            "lat": 38.7223,
            "lng": -9.1393,
            "discoverable": True,
            "led_status_disable": False,
            "led_power_disable": False,
            "max_power": 3500,
            "longpush_time": 1000,
            "factory_reset_from_switch": True,
            "wifirecovery_reboot_enabled": True,
            "debug_enable": False,
            "allow_cross_origin": False,
            "supply_voltage": 0,
            "power_correction": 1,
            "favorites_enabled": True,
            "coiot_enable": True,
            "coiot_update_period": 15,
            "coiot_peer": "10.0.0.2:5683",
            "ap_roaming_enabled": True,
            "ap_roaming_threshold": -70,
            "longpush_duration_ms_min": 800,
            "longpush_duration_ms_max": 3000,
            "multipush_time_between_pushes_ms_max": 500,
            "sntp_server": "pool.ntp.org",
        }

    def test_it_never_includes_mode_in_the_sys_params(self):
        # A mode change reboots the device, so it only ever travels through the
        # restore's dedicated pre-phase, never the sys param batch.
        assert "mode" not in restorable_params("sys", "sys", _gen1_settings())

    def test_it_prefixes_mqtt_params(self):
        # Gen1 has no /settings/mqtt: the settings are mqtt_*-prefixed on /settings.
        assert restorable_params("mqtt", "mqtt", _gen1_settings()) == {
            "mqtt_enable": True,
            "mqtt_server": "10.0.0.1:1883",
            "mqtt_user": "shelly",
            "mqtt_id": "shelly1-DDEEFF",
            "mqtt_clean_session": True,
            "mqtt_retain": False,
            "mqtt_keep_alive": 60,
            "mqtt_max_qos": 0,
            "mqtt_update_period": 30,
            "mqtt_reconnect_timeout_min": 2.0,
            "mqtt_reconnect_timeout_max": 60.0,
        }

    def test_it_extracts_input_settings(self):
        # i3/Button1 expose /settings/input/{i}; the snapshot echoes its params.
        assert restorable_params("input:0", "input", _gen1_settings()) == {
            "name": "Left button",
            "btn_type": "momentary",
            "btn_reverse": 0,
        }

    def test_it_returns_none_for_a_type_without_a_settings_endpoint(self):
        assert restorable_params("script:0", "script", _gen1_settings()) is None

    def test_it_returns_empty_when_the_snapshot_lacks_the_section(self):
        # Relay-bearing models never echo an "inputs" settings section: their
        # input config lives on, and restores with, the owning relay.
        settings = _gen1_settings()
        settings.pop("inputs")

        assert restorable_params("input:0", "input", settings) == {}

    def test_it_returns_empty_when_the_component_index_is_not_captured(self):
        settings = _gen1_settings()
        settings["relays"] = []

        assert restorable_params("switch:0", "switch", settings) == {}


class TestWifiSubresources:
    def test_it_replays_every_captured_wifi_resource_with_the_ap_last(self):
        # The AP goes last: enabling one WiFi mode disables the other on the
        # device, so the resource enabled in the backup must win.
        assert wifi_subresources(_gen1_settings()) == [
            (
                "wifi",
                {
                    "enabled": True,
                    "ssid": "Castle",
                    "ipv4_method": "static",
                    "ip": "192.168.1.100",
                    "gateway": "192.168.1.1",
                    "netmask": "255.255.255.0",
                    "dns": "8.8.8.8",
                },
            ),
            (
                "wifi_sta1",
                {
                    "enabled": False,
                    "ssid": "CastleFallback",
                    "ipv4_method": "dhcp",
                },
            ),
            # The AP SSID is device-fixed and never sent; the AP key, unlike
            # the STA one, is echoed by GET /settings and round-trips.
            ("wifi_ap", {"enabled": False, "key": "appass"}),
        ]

    def test_it_omits_resources_the_snapshot_lacks(self):
        settings = _gen1_settings()
        settings.pop("wifi_sta1")
        settings.pop("wifi_ap")

        assert [subtype for subtype, _ in wifi_subresources(settings)] == ["wifi"]
