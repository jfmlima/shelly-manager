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

    async def test_it_applies_bulk_config_successfully(
        self, use_case, mock_device_gateway, mock_device_status_with_components
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        component_type = "switch"
        config = {"in_mode": "button", "initial_state": "off"}

        mock_device_gateway.get_device_status = AsyncMock(
            return_value=mock_device_status_with_components
        )

        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.SetConfig",
                device_ip="192.168.1.100",
                message="Config applied successfully",
            )
        )

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        # Should have 2 results (1 per device, each device has 1 switch component)
        assert len(results) == 2
        assert all(result.success for result in results)

        # Verify the method was called correctly for both devices
        assert mock_device_gateway.execute_component_action.call_count == 2
        mock_device_gateway.execute_component_action.assert_any_call(
            "192.168.1.100",
            "switch",
            "SetConfig",
            {"config": config},
        )
        mock_device_gateway.execute_component_action.assert_any_call(
            "192.168.1.101",
            "switch",
            "SetConfig",
            {"config": config},
        )

    async def test_it_applies_bulk_config_with_unreachable_device(
        self, use_case, mock_device_gateway, mock_device_status_with_components
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        component_type = "switch"
        config = {"in_mode": "button"}

        # First device succeeds, second device fails
        mock_device_gateway.execute_component_action = AsyncMock(
            side_effect=[
                ActionResult(
                    success=True,
                    action_type="switch.SetConfig",
                    device_ip="192.168.1.100",
                    message="Config applied",
                ),
                ActionResult(
                    success=False,
                    action_type="switch.SetConfig",
                    device_ip="192.168.1.101",
                    message="Device unreachable",
                    error="Connection failed",
                ),
            ]
        )

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        # Should have 2 results (all results are included, both success and failure)
        assert len(results) == 2
        assert results[0].device_ip == "192.168.1.100"
        assert results[0].success is True
        assert results[1].device_ip == "192.168.1.101"
        assert results[1].success is False

    async def test_it_applies_bulk_config_with_component_failures(
        self, use_case, mock_device_gateway, mock_device_status_with_components
    ):
        device_ips = ["192.168.1.100"]
        component_type = "switch"
        config = {"in_mode": "button"}

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

        # Mock the execute_component_action to return a failure for "cover" component type
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=False,
                action_type="cover.SetConfig",
                device_ip="192.168.1.100",
                message="Component type not found",
                error="No cover component found",
            )
        )

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        # Should have 1 result (the failed attempt to configure cover)
        assert len(results) == 1
        assert results[0].success is False
        assert results[0].action_type == "cover.SetConfig"

        # Should be called once with the cover component type
        mock_device_gateway.execute_component_action.assert_called_once_with(
            "192.168.1.100",
            "cover",
            "SetConfig",
            {"config": config},
        )

    async def test_it_applies_bulk_config_multiple_components_same_type(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        component_type = "switch"
        config = {"in_mode": "button"}

        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.SetConfig",
                device_ip="192.168.1.100",
                message="Config applied",
            )
        )

        results = await use_case.apply_bulk_config(device_ips, component_type, config)

        # Should have 1 result (1 per device, regardless of number of components)
        assert len(results) == 1
        assert all(result.success for result in results)

        # Should be called once per device
        assert mock_device_gateway.execute_component_action.call_count == 1
        mock_device_gateway.execute_component_action.assert_called_with(
            "192.168.1.100",
            "switch",
            "SetConfig",
            {"config": config},
        )
