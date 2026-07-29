import asyncio
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.components import (
    Component,
    InputComponent,
    SwitchComponent,
    SystemComponent,
)
from core.domain.entities.device_status import DeviceStatus
from core.domain.entities.exceptions import BulkOperationError
from core.domain.value_objects.action_result import ActionResult
from core.use_cases.bulk_operations import BulkOperationsUseCase


class TestBulkOperationsUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return BulkOperationsUseCase(device_gateway=mock_device_gateway)

    async def test_it_updates_multiple_devices_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.100",
                message="Update successful",
            ),
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.101",
                message="Update successful",
            ),
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_update(device_ips, "stable")

        assert len(results) == 2
        assert all(result.success for result in results)
        mock_device_gateway.execute_bulk_action.assert_called_once_with(
            device_ips, "shelly", "Update", {"channel": "stable"}
        )

    async def test_it_updates_with_beta_channel(self, use_case, mock_device_gateway):
        device_ips = ["192.168.1.100"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.100",
                message="Beta update successful",
            )
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_update(device_ips, "beta")

        assert len(results) == 1
        assert results[0].success is True
        mock_device_gateway.execute_bulk_action.assert_called_once_with(
            device_ips, "shelly", "Update", {"channel": "beta"}
        )

    async def test_it_raises_bulk_operation_error_on_update_failure(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            side_effect=Exception("Gateway error")
        )

        with pytest.raises(BulkOperationError, match="Bulk update failed"):
            await use_case.execute_bulk_update(device_ips)

    async def test_it_reboots_multiple_devices_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="reboot",
                device_ip="192.168.1.100",
                message="Reboot successful",
            ),
            ActionResult(
                success=True,
                action_type="reboot",
                device_ip="192.168.1.101",
                message="Reboot successful",
            ),
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_reboot(device_ips)

        assert len(results) == 2
        assert all(result.success for result in results)
        mock_device_gateway.execute_bulk_action.assert_called_once_with(
            device_ips, "shelly", "Reboot", {}
        )

    async def test_it_raises_bulk_operation_error_on_reboot_failure(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            side_effect=Exception("Gateway error")
        )

        with pytest.raises(BulkOperationError, match="Bulk reboot failed"):
            await use_case.execute_bulk_reboot(device_ips)

    async def test_it_factory_resets_multiple_devices(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="shelly.FactoryReset",
                device_ip="192.168.1.100",
                message="Factory reset completed",
            ),
            ActionResult(
                success=True,
                action_type="shelly.FactoryReset",
                device_ip="192.168.1.101",
                message="Factory reset completed",
            ),
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_factory_reset(device_ips)

        assert len(results) == 2
        assert all(result.success for result in results)
        mock_device_gateway.execute_bulk_action.assert_called_once_with(
            device_ips, "shelly", "FactoryReset", {}
        )

    async def test_it_handles_mixed_results_in_bulk_operations(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="reboot",
                device_ip="192.168.1.100",
                message="Reboot successful",
            ),
            ActionResult(
                success=False,
                action_type="reboot",
                device_ip="192.168.1.101",
                message="Reboot failed",
                error="Device offline",
            ),
            ActionResult(
                success=True,
                action_type="reboot",
                device_ip="192.168.1.102",
                message="Reboot successful",
            ),
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_reboot(device_ips)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert results[1].error == "Device offline"

    async def test_it_handles_empty_device_list_for_bulk_operations(
        self, use_case, mock_device_gateway
    ):
        empty_ips = []
        mock_device_gateway.execute_bulk_action = AsyncMock(return_value=[])

        update_result = await use_case.execute_bulk_update(empty_ips)
        reboot_result = await use_case.execute_bulk_reboot(empty_ips)

        assert update_result == []
        assert reboot_result == []

    @pytest.fixture
    def mock_device_status_with_components(self):
        return DeviceStatus(
            device_ip="192.168.1.100",
            device_name="Test Device",
            device_type="shelly1pm",
            firmware_version="20230913-112003",
            mac_address="AA:BB:CC:DD:EE:FF",
            app_name="switch",
            components=[
                SwitchComponent(
                    key="switch:0",
                    component_type="switch",
                    status={"output": True},
                    config={"in_mode": "flip", "initial_state": "restore_last"},
                    attrs={},
                ),
                InputComponent(
                    key="input:0",
                    component_type="input",
                    status={"state": False},
                    config={"type": "switch", "invert": False},
                    attrs={},
                ),
                SystemComponent(
                    key="sys",
                    component_type="sys",
                    status={},
                    config={"device": {"name": "Test Device"}},
                    attrs={},
                ),
            ],
        )

    async def test_it_exports_bulk_config_successfully(
        self, use_case, mock_device_gateway, mock_device_status_with_components
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        component_types = ["switch", "input"]

        mock_device_gateway.get_device_status = AsyncMock(
            return_value=mock_device_status_with_components
        )

        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.GetConfig",
                device_ip="192.168.1.100",
                message="Config retrieved",
                data={"in_mode": "flip", "initial_state": "restore_last"},
            )
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        assert "export_metadata" in result
        assert "devices" in result
        assert result["export_metadata"]["total_devices"] == 2
        assert result["export_metadata"]["component_types"] == component_types

        device_data = result["devices"]["192.168.1.100"]
        assert "device_info" in device_data
        assert "components" in device_data
        assert device_data["device_info"]["device_name"] == "Test Device"

        assert "switch:0" in device_data["components"]
        assert device_data["components"]["switch:0"]["type"] == "switch"
        assert device_data["components"]["switch:0"]["success"] is True

    async def test_it_exports_bulk_config_with_unreachable_device(
        self, use_case, mock_device_gateway, mock_device_status_with_components
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        component_types = ["switch"]

        mock_device_gateway.get_device_status = AsyncMock(
            side_effect=[mock_device_status_with_components, None]
        )

        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.GetConfig",
                device_ip="192.168.1.100",
                message="Config retrieved",
                data={"in_mode": "flip"},
            )
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        assert len(result["devices"]) == 1
        assert "192.168.1.100" in result["devices"]
        assert "192.168.1.101" not in result["devices"]

    async def test_it_exports_bulk_config_with_component_failures(
        self, use_case, mock_device_gateway, mock_device_status_with_components
    ):
        device_ips = ["192.168.1.100"]
        component_types = ["switch", "input"]

        mock_device_gateway.get_device_status = AsyncMock(
            return_value=mock_device_status_with_components
        )

        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=[
                ActionResult(
                    success=True,
                    action_type="switch.GetConfig",
                    device_ip="192.168.1.100",
                    message="Config retrieved",
                    data={"in_mode": "flip"},
                ),
                ActionResult(
                    success=False,
                    action_type="input.GetConfig",
                    device_ip="192.168.1.100",
                    message="Config retrieval failed",
                    error="Component not accessible",
                ),
            ]
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        device_data = result["devices"]["192.168.1.100"]

        switch_data = device_data["components"]["switch:0"]
        input_data = device_data["components"]["input:0"]

        assert switch_data["success"] is True
        assert switch_data["config"] == {"in_mode": "flip"}
        assert input_data["success"] is False
        assert input_data["error"] == "Component not accessible"

    async def test_it_exports_bulk_config_filters_component_types(
        self, use_case, mock_device_gateway, mock_device_status_with_components
    ):
        device_ips = ["192.168.1.100"]
        component_types = ["switch"]

        mock_device_gateway.get_device_status = AsyncMock(
            return_value=mock_device_status_with_components
        )

        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.GetConfig",
                device_ip="192.168.1.100",
                message="Config retrieved",
                data={"in_mode": "flip"},
            )
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        device_data = result["devices"]["192.168.1.100"]
        components = device_data["components"]

        assert "switch:0" in components
        assert "input:0" not in components
        assert "sys" not in components
        assert len(components) == 1

    async def test_it_exports_multiple_script_components(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_types = ["script"]

        device_status = DeviceStatus(
            device_ip="192.168.1.100",
            device_name="Test Device",
            device_type="shellypro1pm",
            firmware_version="1.0.0",
            mac_address="AA:BB:CC:DD:EE:FF",
            app_name="test",
            components=[
                Component(
                    key="script:0",
                    component_type="script",
                    status={},
                    config={"name": "script_one"},
                    attrs={},
                ),
                Component(
                    key="script:1",
                    component_type="script",
                    status={},
                    config={"name": "script_two"},
                    attrs={},
                ),
            ],
        )

        mock_device_gateway.get_device_status = AsyncMock(return_value=device_status)
        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=[
                ActionResult(
                    success=True,
                    action_type="script.GetConfig",
                    device_ip="192.168.1.100",
                    message="Config retrieved",
                    data={"name": "script_one"},
                ),
                ActionResult(
                    success=True,
                    action_type="script.GetCode",
                    device_ip="192.168.1.100",
                    message="Code retrieved",
                    data={"data": "console.log('Script 1');", "left": 0},
                ),
                ActionResult(
                    success=True,
                    action_type="script.GetConfig",
                    device_ip="192.168.1.100",
                    message="Config retrieved",
                    data={"name": "script_two"},
                ),
                ActionResult(
                    success=True,
                    action_type="script.GetCode",
                    device_ip="192.168.1.100",
                    message="Code retrieved",
                    data={"data": "console.log('Script 2');", "left": 0},
                ),
            ]
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        device_data = result["devices"]["192.168.1.100"]
        assert len(device_data["components"]) == 2

        script_0 = device_data["components"]["script:0"]
        assert script_0["code"] == {"data": "console.log('Script 1');", "left": 0}

        script_1 = device_data["components"]["script:1"]
        assert script_1["code"] == {"data": "console.log('Script 2');", "left": 0}

    async def test_it_exports_schedules_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_types = ["schedules"]

        device_status = DeviceStatus(
            device_ip="192.168.1.100",
            device_name="Test Device",
            device_type="shellypro1pm",
            firmware_version="1.0.0",
            mac_address="AA:BB:CC:DD:EE:FF",
            app_name="test",
            components=[],  # Schedules don't appear here
        )

        mock_device_gateway.get_device_status = AsyncMock(return_value=device_status)
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="schedule.List",
                device_ip="192.168.1.100",
                message="Schedules retrieved",
                data={
                    "jobs": [
                        {
                            "id": 1,
                            "enable": True,
                            "timespec": "0 0 8 * * SUN,MON,TUE,WED,THU,FRI,SAT",
                            "calls": [
                                {
                                    "method": "Switch.Set",
                                    "params": {"id": 0, "on": False},
                                }
                            ],
                        },
                        {
                            "id": 2,
                            "enable": True,
                            "timespec": "0 30 19 * * MON,TUE,WED,THU,FRI",
                            "calls": [
                                {
                                    "method": "Switch.Set",
                                    "params": {"id": 0, "on": True},
                                }
                            ],
                        },
                    ],
                    "rev": 4,
                },
            )
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        # Verify schedule is exported
        device_data = result["devices"]["192.168.1.100"]
        assert "schedules" in device_data["components"]

        schedule = device_data["components"]["schedules"]
        assert schedule["type"] == "schedule"
        assert schedule["success"] is True
        assert schedule["config"]["jobs"] is not None
        assert len(schedule["config"]["jobs"]) == 2
        assert schedule["config"]["rev"] == 4

    async def test_it_exports_schedules_when_list_fails(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_types = ["schedules"]

        device_status = DeviceStatus(
            device_ip="192.168.1.100",
            device_name="Test Device",
            device_type="shellypro1pm",
            firmware_version="1.0.0",
            mac_address="AA:BB:CC:DD:EE:FF",
            app_name="test",
            components=[],
        )

        mock_device_gateway.get_device_status = AsyncMock(return_value=device_status)
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=False,
                action_type="schedule.List",
                device_ip="192.168.1.100",
                message="Failed",
                error="Schedule component not available",
            )
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        # Verify schedule export shows failure
        device_data = result["devices"]["192.168.1.100"]
        assert "schedules" in device_data["components"]

        schedule = device_data["components"]["schedules"]
        assert schedule["type"] == "schedule"
        assert schedule["success"] is False
        assert schedule["config"] is None
        assert schedule["error"] == "Schedule component not available"

    async def test_it_exports_schedules_when_none_exist(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_types = ["schedules"]

        device_status = DeviceStatus(
            device_ip="192.168.1.100",
            device_name="Test Device",
            device_type="shellypro1pm",
            firmware_version="1.0.0",
            mac_address="AA:BB:CC:DD:EE:FF",
            app_name="test",
            components=[],
        )

        mock_device_gateway.get_device_status = AsyncMock(return_value=device_status)
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="schedule.List",
                device_ip="192.168.1.100",
                message="Schedules retrieved",
                data={"jobs": [], "rev": 0},
            )
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        # Verify empty schedule list is exported
        device_data = result["devices"]["192.168.1.100"]
        schedule = device_data["components"]["schedules"]
        assert schedule["success"] is True
        assert schedule["config"]["jobs"] == []
        assert schedule["config"]["rev"] == 0

    async def test_it_exports_mixed_components_with_schedules(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_types = ["switch", "schedules"]

        device_status = DeviceStatus(
            device_ip="192.168.1.100",
            device_name="Test Device",
            device_type="shellypro1pm",
            firmware_version="1.0.0",
            mac_address="AA:BB:CC:DD:EE:FF",
            app_name="test",
            components=[
                Component(
                    key="switch:0",
                    component_type="switch",
                    status={},
                    config={"name": "Main Switch"},
                    attrs={},
                ),
            ],
        )

        mock_device_gateway.get_device_status = AsyncMock(return_value=device_status)
        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=[
                # Switch GetConfig
                ActionResult(
                    success=True,
                    action_type="switch.GetConfig",
                    device_ip="192.168.1.100",
                    message="Config retrieved",
                    data={"name": "Main Switch"},
                ),
                # Schedule.List
                ActionResult(
                    success=True,
                    action_type="schedule.List",
                    device_ip="192.168.1.100",
                    message="Schedules retrieved",
                    data={
                        "jobs": [
                            {
                                "id": 1,
                                "enable": True,
                                "timespec": "0 9 8 * * *",
                                "calls": [],
                            }
                        ],
                        "rev": 1,
                    },
                ),
            ]
        )

        result = await use_case.export_bulk_config(device_ips, component_types)

        # Verify both switch and schedule are exported
        device_data = result["devices"]["192.168.1.100"]
        assert "switch:0" in device_data["components"]
        assert "schedules" in device_data["components"]

        # Verify schedule has jobs
        assert device_data["components"]["schedules"]["config"]["jobs"] is not None
        assert len(device_data["components"]["schedules"]["config"]["jobs"]) == 1

    @pytest.fixture
    def gen1_device_status(self):
        return DeviceStatus(
            device_ip="192.168.1.100",
            device_name="Gen1 Relay",
            device_type="SHSW-1",
            firmware_version="20230913-112003/v1.14.0",
            mac_address="AABBCCDDEEFF",
            app_name="switch",
            gen=1,
            components=[
                SwitchComponent(
                    key="switch:0",
                    component_type="switch",
                    status={"output": False},
                    config={
                        "name": "Relay",
                        "auto_off": True,
                        "auto_off_delay": 30.0,
                    },
                    attrs={},
                ),
                SystemComponent(
                    key="sys",
                    component_type="sys",
                    status={},
                    config={"device": {"name": "Gen1 Relay"}},
                    attrs={},
                ),
            ],
        )

    async def test_it_exports_gen1_config_from_mapped_components_without_rpc(
        self, use_case, mock_device_gateway, gen1_device_status
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=gen1_device_status
        )
        mock_device_gateway.execute_component_action = AsyncMock()
        raw_settings = {"relays": [{"auto_off": 30}], "name": "Gen1 Relay"}
        mock_device_gateway.get_legacy_settings = AsyncMock(return_value=raw_settings)

        result = await use_case.export_bulk_config(
            ["192.168.1.100"], ["switch", "sys", "schedules"]
        )

        mock_device_gateway.execute_component_action.assert_not_called()

        components = result["devices"]["192.168.1.100"]["components"]
        assert components["switch:0"]["success"] is True
        assert components["switch:0"]["error"] is None
        assert components["switch:0"]["config"] == {
            "name": "Relay",
            "auto_off": True,
            "auto_off_delay": 30.0,
        }
        assert components["sys"]["success"] is True

        assert components["legacy_settings"]["type"] == "legacy_settings"
        assert components["legacy_settings"]["success"] is True
        assert components["legacy_settings"]["config"] == raw_settings
        mock_device_gateway.get_legacy_settings.assert_awaited_once_with(
            "192.168.1.100"
        )

    async def test_it_omits_legacy_settings_when_raw_fetch_fails(
        self, use_case, mock_device_gateway, gen1_device_status
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=gen1_device_status
        )
        mock_device_gateway.execute_component_action = AsyncMock()
        mock_device_gateway.get_legacy_settings = AsyncMock(return_value=None)

        result = await use_case.export_bulk_config(["192.168.1.100"], ["switch"])

        components = result["devices"]["192.168.1.100"]["components"]
        assert "legacy_settings" not in components
        assert components["switch:0"]["success"] is True
        mock_device_gateway.execute_component_action.assert_not_called()

    async def test_it_filters_gen1_components_by_requested_type(
        self, use_case, mock_device_gateway, gen1_device_status
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=gen1_device_status
        )
        mock_device_gateway.execute_component_action = AsyncMock()
        mock_device_gateway.get_legacy_settings = AsyncMock(return_value=None)

        result = await use_case.export_bulk_config(["192.168.1.100"], ["switch"])

        components = result["devices"]["192.168.1.100"]["components"]
        assert "switch:0" in components
        assert "sys" not in components

    async def test_it_applies_bulk_config_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        component_type = "switch"
        config = {"in_mode": "button", "initial_state": "off"}

        mock_device_gateway.get_component_keys = AsyncMock(return_value=["switch:0"])

        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.SetConfig",
                device_ip="192.168.1.100",
                message="Config applied successfully",
            )
        )

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        assert len(results) == 2
        assert all(result.success for result in results)

        assert mock_device_gateway.execute_component_action.call_count == 2
        mock_device_gateway.execute_component_action.assert_any_call(
            "192.168.1.100",
            "switch:0",
            "SetConfig",
            {"config": config},
        )
        mock_device_gateway.execute_component_action.assert_any_call(
            "192.168.1.101",
            "switch:0",
            "SetConfig",
            {"config": config},
        )

    async def test_it_applies_bulk_config_with_unreachable_device(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        component_type = "switch"
        config = {"in_mode": "button"}

        # First device has components, second returns empty (unreachable)
        mock_device_gateway.get_component_keys = AsyncMock(
            side_effect=[["switch:0"], []]
        )

        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.SetConfig",
                device_ip="192.168.1.100",
                message="Config applied",
            )
        )

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].device_ip == "192.168.1.101"
        assert results[1].success is False

    async def test_it_applies_bulk_config_with_component_failures(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_type = "switch"
        config = {"in_mode": "button"}

        mock_device_gateway.get_component_keys = AsyncMock(return_value=["switch:0"])

        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=False,
                action_type="switch.SetConfig",
                device_ip="192.168.1.100",
                message="Config apply failed",
                error="Invalid configuration",
            )
        )

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        # Should have 1 result (all results are included, even failed ones)
        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error == "Invalid configuration"

    async def test_it_applies_bulk_config_filters_by_component_type(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_type = "cover"
        config = {"motor": {"idle_power_thr": 2.0}}

        # No cover components found
        mock_device_gateway.get_component_keys = AsyncMock(return_value=[])

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].action_type == "cover.SetConfig"
        assert "No cover components found" in results[0].message

        mock_device_gateway.execute_component_action.assert_not_called()

    async def test_it_applies_bulk_config_multiple_components_same_type(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_type = "switch"
        config = {"in_mode": "button"}

        mock_device_gateway.get_component_keys = AsyncMock(
            return_value=["switch:0", "switch:1"]
        )
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.SetConfig",
                device_ip="192.168.1.100",
                message="Config applied",
            )
        )

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        assert len(results) == 2
        assert all(result.success for result in results)

        assert mock_device_gateway.execute_component_action.call_count == 2
        mock_device_gateway.execute_component_action.assert_any_call(
            "192.168.1.100",
            "switch:0",
            "SetConfig",
            {"config": config},
        )
        mock_device_gateway.execute_component_action.assert_any_call(
            "192.168.1.100",
            "switch:1",
            "SetConfig",
            {"config": config},
        )

    async def test_it_exports_devices_concurrently(self, use_case, mock_device_gateway):
        # The first device's status fetch only completes once the second has
        # run, so a sequential export deadlocks and times out here.
        first_started = asyncio.Event()
        second_done = asyncio.Event()

        async def get_status(device_ip):
            if device_ip == "192.168.1.100":
                first_started.set()
                await asyncio.wait_for(second_done.wait(), timeout=1)
            else:
                await first_started.wait()
                second_done.set()
            return DeviceStatus(device_ip=device_ip, components=[])

        mock_device_gateway.get_device_status = AsyncMock(side_effect=get_status)

        result = await use_case.export_bulk_config(
            ["192.168.1.100", "192.168.1.101"], []
        )

        assert list(result["devices"]) == ["192.168.1.100", "192.168.1.101"]

    async def test_it_lets_every_capture_finish_before_a_failure_surfaces(
        self, use_case, mock_device_gateway
    ):
        # A device that raises must not leave its siblings running against real
        # hardware with nobody awaiting them.
        finished = []

        async def get_status(device_ip):
            if device_ip == "192.168.1.100":
                raise RuntimeError("boom")
            await asyncio.sleep(0.05)
            finished.append(device_ip)
            return None

        mock_device_gateway.get_device_status = AsyncMock(side_effect=get_status)

        with pytest.raises(RuntimeError, match="boom"):
            await use_case.export_bulk_config(["192.168.1.100", "192.168.1.101"], [])

        assert finished == ["192.168.1.101"]

    async def test_it_applies_config_concurrently_and_keeps_device_order(
        self, use_case, mock_device_gateway
    ):
        first_started = asyncio.Event()
        second_done = asyncio.Event()

        async def get_component_keys(device_ip, component_type):
            if device_ip == "192.168.1.100":
                first_started.set()
                await asyncio.wait_for(second_done.wait(), timeout=1)
            else:
                await first_started.wait()
                second_done.set()
            return [f"{component_type}:0"]

        mock_device_gateway.get_component_keys = AsyncMock(
            side_effect=get_component_keys
        )
        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=lambda device_ip, key, action, parameters: ActionResult(
                success=True,
                action_type=f"{key}.SetConfig",
                device_ip=device_ip,
                message="Config applied",
            )
        )

        results = await use_case.apply_bulk_config(
            ["192.168.1.100", "192.168.1.101"], "switch", {}
        )

        assert [result.device_ip for result in results] == [
            "192.168.1.100",
            "192.168.1.101",
        ]
