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
        mock_device_gateway.execute_component_action.assert_not_called()

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
        # Aborted after the failed clear — no Create attempted.
        assert actions == ["DeleteAll"]
        assert result.success is False
        sched = next(c for c in result.components if c.key == "schedules")
        assert sched.success is False

    async def test_it_reports_unknown_keys_on_gen1_path(
        self, use_case, mock_device_gateway, mock_repository
    ):
        mock_repository.get = AsyncMock(return_value=_backup(generation="gen1"))

        result = await use_case.restore(1, IP, component_keys=["sys", "bogus:9"])

        reasons = {c.key: c.skipped_reason for c in result.components}
        assert set(reasons) == {"sys", "bogus:9"}
        assert reasons["bogus:9"] == "not present in backup"
        assert "Gen1 restore not supported" in reasons["sys"]
        mock_device_gateway.execute_component_action.assert_not_called()
