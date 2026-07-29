from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.device_backup import DeviceBackup
from core.domain.entities.exceptions import DeviceNotFoundError
from core.domain.value_objects.action_result import ActionResult
from core.use_cases.backup_device_config import BackupNotFoundError
from core.use_cases.restore_device_config import (
    DeviceMismatchError,
    RestoreDeviceConfig,
)

IP = "192.168.1.100"


def _snapshot():
    return {
        "device_info": {"mac_address": "AABBCCDDEEFF"},
        "components": {
            "switch:0": {
                "type": "switch",
                "success": True,
                "config": {"id": 0, "cfg_rev": 5, "name": "Kitchen"},
            },
            "sys": {
                "type": "sys",
                "success": True,
                "config": {"device": {"mac": "AABBCCDDEEFF", "name": "X"}},
            },
            "wifi": {
                "type": "wifi",
                "success": True,
                "config": {"ap": {"is_open": False, "enable": True}},
            },
        },
    }


def _backup(generation="gen2"):
    return DeviceBackup(
        device_mac="AABBCCDDEEFF",
        snapshot=_snapshot(),
        generation=generation,
        id=1,
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


GEN1_KEYS = ("sys", "wifi", "cloud", "mqtt", "switch:0", "cover:0", "input:0")


def _gen1_backup(settings=None, with_settings_entry=True):
    """A Gen1 backup: Gen2-shaped mapped configs plus the raw /settings entry."""
    components = {
        key: {"type": key.split(":")[0], "success": True, "config": {"name": "mapped"}}
        for key in GEN1_KEYS
    }
    if with_settings_entry:
        components["legacy_settings"] = {
            "type": "legacy_settings",
            "success": True,
            "config": _gen1_settings() if settings is None else settings,
        }
    return DeviceBackup(
        device_mac="AABBCCDDEEFF",
        snapshot={
            "device_info": {"mac_address": "AABBCCDDEEFF"},
            "components": components,
        },
        generation="gen1",
        id=1,
    )


def _status(
    mac="AA:BB:CC:DD:EE:FF",
    keys=("switch:0", "sys", "wifi"),
    app_name="Plus1PM",
    gen=2,
):
    return SimpleNamespace(
        mac_address=mac,
        app_name=app_name,
        gen=gen,
        components=[SimpleNamespace(key=k) for k in keys],
    )


def _ok(key):
    return ActionResult(
        success=True, action_type=f"{key}.SetConfig", device_ip=IP, message="ok"
    )


class TestRestoreDeviceConfig:
    @pytest.fixture
    def mock_repository(self):
        repo = AsyncMock()
        repo.get = AsyncMock(return_value=_backup())
        return repo

    @pytest.fixture
    def use_case(self, mock_device_gateway, mock_repository):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=lambda ip, key, action, params: _ok(key)
        )
        return RestoreDeviceConfig(
            device_gateway=mock_device_gateway,
            repository_factory=repository_factory,
        )

    async def test_it_excludes_network_components_by_default(
        self, use_case, mock_device_gateway
    ):
        result = await use_case.restore(1, IP)

        restored = {
            call.args[1]
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "SetConfig"
        }
        assert restored == {"switch:0", "sys"}
        assert result.success is True
        # wifi is a network component, excluded by default (not selected at all)
        assert "wifi" not in {c.key for c in result.components}

    async def test_it_strips_readonly_fields(self, use_case, mock_device_gateway):
        await use_case.restore(1, IP, component_keys=["switch:0", "sys", "wifi"])

        by_key = {
            call.args[1]: call.args[3]["config"]
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "SetConfig"
        }
        assert "id" not in by_key["switch:0"]
        assert "cfg_rev" not in by_key["switch:0"]
        assert "mac" not in by_key["sys"]["device"]
        assert "is_open" not in by_key["wifi"]["ap"]

    async def test_it_orders_network_components_last(
        self, use_case, mock_device_gateway
    ):
        await use_case.restore(1, IP, component_keys=["wifi", "switch:0", "sys"])

        order = [
            call.args[1]
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "SetConfig"
        ]
        assert order[-1] == "wifi"

    async def test_it_raises_on_mac_mismatch(self, use_case, mock_device_gateway):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(mac="FFFFFFFFFFFF")
        )

        with pytest.raises(DeviceMismatchError):
            await use_case.restore(1, IP)

    async def test_it_allows_mac_mismatch_when_overridden(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(mac="FFFFFFFFFFFF")
        )

        result = await use_case.restore(1, IP, allow_mac_mismatch=True)

        assert result.total > 0

    async def test_it_records_per_component_failure(
        self, use_case, mock_device_gateway
    ):
        def side_effect(ip, key, action, params):
            if key == "switch:0":
                return ActionResult(
                    success=False,
                    action_type="switch:0.SetConfig",
                    device_ip=IP,
                    message="bad",
                    error="rejected",
                )
            return _ok(key)

        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=side_effect
        )

        result = await use_case.restore(1, IP, component_keys=["switch:0", "sys"])

        assert result.failed == 1
        assert result.succeeded == 1
        assert result.success is False

    async def test_it_skips_components_absent_on_target(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(keys=("sys",))
        )

        result = await use_case.restore(1, IP, component_keys=["switch:0", "sys"])

        skipped = {c.key for c in result.components if c.skipped}
        assert "switch:0" in skipped

    async def test_it_reboots_after_successful_restore(
        self, use_case, mock_device_gateway
    ):
        await use_case.restore(1, IP, component_keys=["sys"], reboot=True)

        reboot_calls = [
            call
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "Reboot"
        ]
        assert len(reboot_calls) == 1

    async def test_it_skips_all_for_gen1(
        self, use_case, mock_device_gateway, mock_repository
    ):
        mock_repository.get = AsyncMock(return_value=_backup(generation="gen1"))

        result = await use_case.restore(1, IP)

        assert result.skipped == len(result.components)
        assert result.success is False
        # Mirrors the default selection: network components are not reported.
        assert "wifi" not in {c.key for c in result.components}
        mock_device_gateway.execute_component_action.assert_not_called()

    async def test_it_reports_a_missing_legacy_settings_request_as_not_in_backup(
        self, use_case
    ):
        result = await use_case.restore(1, IP, component_keys=["legacy_settings"])

        entry = next(c for c in result.components if c.key == "legacy_settings")
        assert entry.skipped is True
        assert entry.skipped_reason == "not present in backup"

    async def test_it_raises_when_backup_missing(self, use_case, mock_repository):
        mock_repository.get = AsyncMock(return_value=None)

        with pytest.raises(BackupNotFoundError):
            await use_case.restore(99, IP)

    async def test_it_raises_when_device_unreachable(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        with pytest.raises(DeviceNotFoundError):
            await use_case.restore(1, IP)

    async def test_it_is_not_successful_and_does_not_reboot_for_noop_restore(
        self, use_case, mock_device_gateway
    ):
        # Every requested key is unknown -> nothing applied.
        result = await use_case.restore(1, IP, component_keys=["bogus:9"], reboot=True)

        assert result.success is False
        assert result.succeeded == 0
        assert result.message == "No components were applied"
        reboot_calls = [
            call
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "Reboot"
        ]
        assert reboot_calls == []

    async def test_it_restores_an_empty_script_body(
        self, use_case, mock_device_gateway, mock_repository
    ):
        backup = _backup()
        backup.snapshot["components"]["script:1"] = {
            "type": "script",
            "success": True,
            "config": {"id": 1, "enable": True},
            "code": {"data": ""},
        }
        mock_repository.get = AsyncMock(return_value=backup)
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(keys=("sys", "script:1"))
        )

        result = await use_case.restore(1, IP, component_keys=["script:1"])

        put_calls = [
            call
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "PutCode"
        ]
        assert len(put_calls) == 1
        assert put_calls[0].args[3]["code"] == ""
        assert any(c.key == "script:1" and c.success for c in result.components)

    async def test_it_reports_unknown_requested_keys_as_skipped(self, use_case):
        result = await use_case.restore(1, IP, component_keys=["switch:0", "bogus:9"])

        bogus = next(c for c in result.components if c.key == "bogus:9")
        assert bogus.skipped is True
        assert bogus.skipped_reason == "not present in backup"
        # the real key still restored
        assert any(c.key == "switch:0" and c.success for c in result.components)

    async def test_it_reports_a_corrupt_entry_rather_than_calling_it_absent(
        self, use_case, mock_repository
    ):
        backup = _backup()
        backup.snapshot["components"]["switch:0"] = "corrupt"
        mock_repository.get = AsyncMock(return_value=backup)

        result = await use_case.restore(1, IP, component_keys=["switch:0"])

        entry = next(c for c in result.components if c.key == "switch:0")
        assert entry.skipped is True
        assert entry.skipped_reason != "not present in backup"

    async def test_it_short_circuits_when_target_is_gen1(
        self, use_case, mock_device_gateway
    ):
        # Gen2 backup, but the live target reports as Gen1 (gen == 1).
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status(gen=1))

        result = await use_case.restore(1, IP, allow_mac_mismatch=True)

        assert result.success is False
        assert result.skipped == len(result.components)
        mock_device_gateway.execute_component_action.assert_not_called()

    async def test_it_uses_snapshot_mac_for_identity_check(
        self, use_case, mock_repository
    ):
        # Snapshot says a different device than the (matching) target MAC.
        backup = _backup()
        backup.snapshot["device_info"]["mac_address"] = "FFFFFFFFFFFF"
        mock_repository.get = AsyncMock(return_value=backup)

        with pytest.raises(DeviceMismatchError) as exc:
            await use_case.restore(1, IP)
        assert exc.value.expected_mac == "FFFFFFFFFFFF"

    async def test_it_replaces_schedules_before_creating(
        self, use_case, mock_device_gateway, mock_repository
    ):
        backup = _backup()
        backup.snapshot["components"]["schedules"] = {
            "type": "schedule",
            "success": True,
            "config": {"jobs": [{"id": 1, "enable": True, "timespec": "0 0 * * *"}]},
        }
        mock_repository.get = AsyncMock(return_value=backup)

        await use_case.restore(1, IP, component_keys=["schedules"])

        actions = [
            call.args[2]
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[1] == "schedule"
        ]
        assert actions == ["DeleteAll", "Create"]

    async def test_it_clears_schedules_when_backup_has_none(
        self, use_case, mock_device_gateway, mock_repository
    ):
        # Device with zero schedules is captured as {"jobs": []}; restoring it
        # must still clear the target (replace semantics), issuing DeleteAll.
        backup = _backup()
        backup.snapshot["components"]["schedules"] = {
            "type": "schedule",
            "success": True,
            "config": {"jobs": [], "rev": 0},
        }
        mock_repository.get = AsyncMock(return_value=backup)

        await use_case.restore(1, IP, component_keys=["schedules"])

        actions = [
            call.args[2]
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[1] == "schedule"
        ]
        assert actions == ["DeleteAll"]

    async def test_it_aborts_schedule_restore_when_clear_fails(
        self, use_case, mock_device_gateway, mock_repository
    ):
        backup = _backup()
        backup.snapshot["components"]["schedules"] = {
            "type": "schedule",
            "success": True,
            "config": {"jobs": [{"id": 1, "enable": True, "timespec": "0 0 * * *"}]},
        }
        mock_repository.get = AsyncMock(return_value=backup)

        def side_effect(ip, key, action, params):
            if action == "DeleteAll":
                return ActionResult(
                    success=False,
                    action_type="schedule.DeleteAll",
                    device_ip=IP,
                    message="bad",
                    error="busy",
                )
            return _ok(key)

        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=side_effect
        )

        result = await use_case.restore(1, IP, component_keys=["schedules"])

        actions = [
            call.args[2]
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[1] == "schedule"
        ]
        # Aborted after the failed clear; no Create attempted.
        assert actions == ["DeleteAll"]
        assert result.success is False
        sched = next(c for c in result.components if c.key == "schedules")
        assert sched.success is False

    async def test_it_reports_unknown_keys_on_generation_mismatch(
        self, use_case, mock_device_gateway, mock_repository
    ):
        mock_repository.get = AsyncMock(return_value=_backup(generation="gen1"))

        result = await use_case.restore(1, IP, component_keys=["sys", "bogus:9"])

        reasons = {c.key: c.skipped_reason for c in result.components}
        assert set(reasons) == {"sys", "bogus:9"}
        assert reasons["bogus:9"] == "not present in backup"
        assert "generation does not match" in reasons["sys"]
        mock_device_gateway.execute_component_action.assert_not_called()


class TestRestoreGen1DeviceConfig:
    """Gen1 restore replays the raw /settings snapshot over Gen1 HTTP endpoints."""

    @pytest.fixture
    def mock_repository(self):
        repo = AsyncMock()
        repo.get = AsyncMock(return_value=_gen1_backup())
        return repo

    @pytest.fixture
    def use_case(self, mock_device_gateway, mock_repository):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(keys=GEN1_KEYS, app_name="SHSW-1", gen=1)
        )
        # Target mode matches the backup, so no mode pre-phase by default.
        mock_device_gateway.get_legacy_settings = AsyncMock(
            return_value={"mode": "relay"}
        )
        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=lambda ip, key, action, params: _ok(key)
        )
        return RestoreDeviceConfig(
            device_gateway=mock_device_gateway,
            repository_factory=repository_factory,
        )

    def _sent(self, mock_device_gateway):
        return {
            call.args[1]: call.args[3]
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "Legacy.SetConfig"
        }

    async def test_it_restores_the_fallback_sta_and_ap_with_the_primary(
        self, use_case, mock_device_gateway
    ):
        result = await use_case.restore(1, IP, component_keys=["wifi"])

        sent = self._sent(mock_device_gateway)
        assert list(sent) == ["wifi", "wifi_sta1", "wifi_ap"]
        assert [c.key for c in result.components] == ["wifi"]
        assert result.success is True

    async def test_it_only_replays_captured_wifi_resources(
        self, use_case, mock_device_gateway, mock_repository
    ):
        settings = _gen1_settings()
        settings.pop("wifi_sta1")
        settings.pop("wifi_ap")
        mock_repository.get = AsyncMock(return_value=_gen1_backup(settings=settings))

        result = await use_case.restore(1, IP, component_keys=["wifi"])

        assert set(self._sent(mock_device_gateway)) == {"wifi"}
        assert result.success is True

    async def test_it_reports_a_failing_wifi_subresource(
        self, use_case, mock_device_gateway
    ):
        def side_effect(ip, key, action, params):
            if key == "wifi_ap":
                return ActionResult(
                    success=False,
                    action_type="wifi_ap.Legacy.SetConfig",
                    device_ip=IP,
                    message="bad",
                    error="Bad Request",
                )
            return _ok(key)

        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=side_effect
        )

        result = await use_case.restore(1, IP, component_keys=["wifi"])

        assert result.success is False
        entry = next(c for c in result.components if c.key == "wifi")
        assert entry.success is False
        assert entry.error == "wifi_ap: Bad Request"

    async def test_it_excludes_network_components_by_default(
        self, use_case, mock_device_gateway
    ):
        result = await use_case.restore(1, IP)

        assert set(self._sent(mock_device_gateway)) == {
            "sys",
            "switch:0",
            "cover:0",
            "input:0",
        }
        assert result.success is True

    async def test_it_orders_network_components_last(
        self, use_case, mock_device_gateway
    ):
        await use_case.restore(
            1, IP, component_keys=["wifi", "mqtt", "switch:0", "sys", "cloud"]
        )

        order = list(self._sent(mock_device_gateway))
        assert order[:2] == ["switch:0", "sys"]
        assert set(order[2:]) == {"wifi", "wifi_sta1", "wifi_ap", "mqtt", "cloud"}

    async def test_it_skips_everything_when_the_snapshot_lacks_raw_settings(
        self, use_case, mock_device_gateway, mock_repository
    ):
        mock_repository.get = AsyncMock(
            return_value=_gen1_backup(with_settings_entry=False)
        )

        result = await use_case.restore(1, IP)

        assert result.success is False
        assert result.skipped == len(result.components)
        assert result.message == "snapshot lacks raw Gen1 settings"
        # The default selection never restores network components, so they are
        # not reported as skipped either.
        assert {"wifi", "mqtt", "cloud"}.isdisjoint({c.key for c in result.components})
        mock_device_gateway.execute_component_action.assert_not_called()

    async def test_it_never_restores_the_legacy_settings_entry(
        self, use_case, mock_device_gateway
    ):
        result = await use_case.restore(1, IP, component_keys=["legacy_settings"])

        # It is the data source, not a component that exists on the device.
        assert self._sent(mock_device_gateway) == {}
        entry = next(c for c in result.components if c.key == "legacy_settings")
        assert entry.skipped is True
        assert entry.skipped_reason == "not a restorable component"

    async def test_it_skips_inputs_when_the_snapshot_has_no_input_settings(
        self, use_case, mock_device_gateway, mock_repository
    ):
        # Relay-bearing models never echo an "inputs" settings section: their
        # input config lives on, and restores with, the owning relay.
        settings = _gen1_settings()
        settings.pop("inputs")
        mock_repository.get = AsyncMock(return_value=_gen1_backup(settings=settings))

        result = await use_case.restore(1, IP, component_keys=["input:0"])

        assert self._sent(mock_device_gateway) == {}
        entry = next(c for c in result.components if c.key == "input:0")
        assert entry.skipped is True
        assert entry.skipped_reason == "no restorable settings captured in backup"

    async def test_it_skips_a_component_missing_from_the_captured_settings(
        self, use_case, mock_device_gateway, mock_repository
    ):
        settings = _gen1_settings()
        settings["relays"] = []
        mock_repository.get = AsyncMock(return_value=_gen1_backup(settings=settings))

        result = await use_case.restore(1, IP, component_keys=["switch:0"])

        assert self._sent(mock_device_gateway) == {}
        entry = next(c for c in result.components if c.key == "switch:0")
        assert entry.skipped_reason == "no restorable settings captured in backup"

    async def test_it_skips_components_absent_on_the_target(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(keys=("sys",), gen=1)
        )

        result = await use_case.restore(1, IP, component_keys=["switch:0", "sys"])

        entry = next(c for c in result.components if c.key == "switch:0")
        assert entry.skipped_reason == "component not present on target device"

    async def test_it_reboots_via_the_legacy_endpoint(
        self, use_case, mock_device_gateway
    ):
        await use_case.restore(1, IP, component_keys=["sys"], reboot=True)

        reboots = [
            call.args[1:3]
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "Legacy.Reboot"
        ]
        assert reboots == [("sys", "Legacy.Reboot")]

    async def test_it_does_not_reboot_when_nothing_was_applied(
        self, use_case, mock_device_gateway, mock_repository
    ):
        settings = _gen1_settings()
        settings.pop("inputs")
        mock_repository.get = AsyncMock(return_value=_gen1_backup(settings=settings))

        result = await use_case.restore(1, IP, component_keys=["input:0"], reboot=True)

        assert result.success is False
        assert mock_device_gateway.execute_component_action.call_args_list == []

    async def test_it_records_per_component_failure(
        self, use_case, mock_device_gateway
    ):
        def side_effect(ip, key, action, params):
            if key == "switch:0":
                return ActionResult(
                    success=False,
                    action_type="switch:0.Legacy.SetConfig",
                    device_ip=IP,
                    message="bad",
                    error="Bad Request",
                )
            return _ok(key)

        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=side_effect
        )

        result = await use_case.restore(1, IP, component_keys=["switch:0", "sys"])

        assert (result.succeeded, result.failed) == (1, 1)
        assert result.success is False
        failed = next(c for c in result.components if c.key == "switch:0")
        assert failed.action == "Legacy.SetConfig"
        assert failed.error == "Bad Request"

    async def test_it_refuses_a_gen1_backup_on_a_gen2_target(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(keys=GEN1_KEYS, gen=2)
        )

        result = await use_case.restore(1, IP)

        assert result.success is False
        assert result.message == "Backup and device generations differ"
        mock_device_gateway.execute_component_action.assert_not_called()

    async def test_it_switches_mode_before_restoring(
        self, use_case, mock_device_gateway, mock_repository
    ):
        # Backup taken in roller mode; the target boots in relay mode and only
        # enumerates its cover component after the mode change reboots it.
        settings = _gen1_settings()
        settings["mode"] = "roller"
        mock_repository.get = AsyncMock(return_value=_gen1_backup(settings=settings))
        mock_device_gateway.get_device_status = AsyncMock(
            side_effect=[
                _status(keys=("sys", "switch:0", "switch:1"), gen=1),
                _status(keys=("sys", "cover:0"), gen=1),
            ]
        )
        mock_device_gateway.get_legacy_settings = AsyncMock(
            return_value={"mode": "relay"}
        )

        result = await use_case.restore(1, IP, component_keys=["cover:0"])

        calls = [
            (call.args[1], call.args[3])
            for call in mock_device_gateway.execute_component_action.call_args_list
            if call.args[2] == "Legacy.SetConfig"
        ]
        assert calls[0] == ("sys", {"mode": "roller"})
        assert calls[1][0] == "cover:0"
        mode_entry = next(c for c in result.components if c.key == "mode")
        assert mode_entry.success is True
        assert result.success is True

    async def test_it_skips_the_mode_phase_when_modes_match(
        self, use_case, mock_device_gateway
    ):
        result = await use_case.restore(1, IP, component_keys=["sys"])

        assert "mode" not in {c.key for c in result.components}
        assert mock_device_gateway.get_device_status.await_count == 1

    async def test_it_skips_the_mode_phase_when_the_backup_lacks_a_mode(
        self, use_case, mock_device_gateway, mock_repository
    ):
        settings = _gen1_settings()
        settings.pop("mode")
        mock_repository.get = AsyncMock(return_value=_gen1_backup(settings=settings))

        result = await use_case.restore(1, IP, component_keys=["sys"])

        mock_device_gateway.get_legacy_settings.assert_not_called()
        assert "mode" not in {c.key for c in result.components}

    async def test_it_reports_when_the_target_mode_cannot_be_read(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_legacy_settings = AsyncMock(return_value=None)

        result = await use_case.restore(1, IP, component_keys=["switch:0"])

        # Surfaced as a skip rather than silently proceeding blind, and the
        # rest of the restore still runs.
        entry = next(c for c in result.components if c.key == "mode")
        assert entry.skipped is True
        assert entry.skipped_reason == "could not read the target device mode"
        assert "switch:0" in self._sent(mock_device_gateway)
        assert result.success is True

    async def test_it_fails_the_restore_when_the_mode_change_fails(
        self, use_case, mock_device_gateway, mock_repository
    ):
        settings = _gen1_settings()
        settings["mode"] = "roller"
        mock_repository.get = AsyncMock(return_value=_gen1_backup(settings=settings))
        mock_device_gateway.get_legacy_settings = AsyncMock(
            return_value={"mode": "relay"}
        )

        def side_effect(ip, key, action, params):
            if params == {"mode": "roller"}:
                return ActionResult(
                    success=False,
                    action_type="sys.Legacy.SetConfig",
                    device_ip=IP,
                    message="bad",
                    error="Bad Request",
                )
            return _ok(key)

        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=side_effect
        )

        result = await use_case.restore(1, IP)

        assert result.success is False
        assert (result.total, result.failed) == (1, 1)
        assert result.message == "Bad Request"
        assert len(mock_device_gateway.execute_component_action.call_args_list) == 1

    async def test_it_fails_when_the_device_never_returns_after_the_mode_change(
        self, mock_device_gateway, mock_repository
    ):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        settings = _gen1_settings()
        settings["mode"] = "roller"
        mock_repository.get = AsyncMock(return_value=_gen1_backup(settings=settings))
        mock_device_gateway.get_device_status = AsyncMock(
            side_effect=[_status(keys=GEN1_KEYS, gen=1)] + [None] * 50
        )
        mock_device_gateway.get_legacy_settings = AsyncMock(
            return_value={"mode": "relay"}
        )
        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=lambda ip, key, action, params: _ok(key)
        )
        use_case = RestoreDeviceConfig(
            device_gateway=mock_device_gateway,
            repository_factory=repository_factory,
            mode_change_timeout=0.05,
            mode_change_poll_interval=0.01,
        )

        result = await use_case.restore(1, IP)

        assert result.success is False
        assert result.message == "device did not come back after the mode change"
        assert (result.total, result.failed) == (1, 1)
