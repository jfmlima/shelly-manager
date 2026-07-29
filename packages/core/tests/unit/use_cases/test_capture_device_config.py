from unittest.mock import AsyncMock

import pytest
from core.domain.entities.components import SwitchComponent
from core.domain.entities.device_status import DeviceStatus
from core.domain.value_objects.action_result import ActionResult
from core.use_cases.capture_device_config import CaptureDeviceConfig


def _status(gen=2):
    return DeviceStatus(
        device_ip="192.168.1.100",
        device_name="Test Device",
        device_type="SNSW-001P16EU",
        firmware_version="1.0.0",
        mac_address="AA:BB:CC:DD:EE:FF",
        app_name="Plus1PM",
        gen=gen,
        components=[
            SwitchComponent(
                key="switch:0",
                component_type="switch",
                status={"output": True},
                config={"name": "Relay"},
                attrs={},
            )
        ],
    )


class TestCaptureDeviceConfig:
    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return CaptureDeviceConfig(device_gateway=mock_device_gateway)

    async def test_it_carries_the_device_identity_into_the_snapshot(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.GetConfig",
                device_ip="192.168.1.100",
                message="ok",
                data={"name": "Relay"},
            )
        )

        snapshot = await use_case.capture("192.168.1.100", _status(), ["switch"])

        assert snapshot.device_info.device_name == "Test Device"
        assert snapshot.device_info.mac_address == "AA:BB:CC:DD:EE:FF"
        assert snapshot.device_info.app_name == "Plus1PM"
        assert snapshot.components["switch:0"].config == {"name": "Relay"}

    async def test_it_captures_gen2_devices_over_rpc(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="switch.GetConfig",
                device_ip="192.168.1.100",
                message="ok",
                data={"name": "From RPC"},
            )
        )

        snapshot = await use_case.capture("192.168.1.100", _status(gen=2), ["switch"])

        assert snapshot.components["switch:0"].config == {"name": "From RPC"}
        mock_device_gateway.execute_component_action.assert_awaited_once_with(
            "192.168.1.100", "switch:0", "GetConfig", {}
        )

    async def test_it_captures_gen1_devices_from_the_mapped_status(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.execute_component_action = AsyncMock()
        mock_device_gateway.get_legacy_settings = AsyncMock(
            return_value={"relays": [{"auto_off": 30}]}
        )

        snapshot = await use_case.capture("192.168.1.100", _status(gen=1), ["switch"])

        assert snapshot.components["switch:0"].config == {"name": "Relay"}
        assert snapshot.legacy_settings == {"relays": [{"auto_off": 30}]}
        mock_device_gateway.execute_component_action.assert_not_awaited()

    async def test_it_leaves_schedules_out_when_the_device_has_none_to_report(
        self, use_case, mock_device_gateway
    ):
        # A successful listing with no payload is a device with nothing to say,
        # not a failed capture: restore must not see a "schedules" entry at all.
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="schedule.List",
                device_ip="192.168.1.100",
                message="ok",
                data=None,
            )
        )

        snapshot = await use_case.capture("192.168.1.100", _status(), ["schedules"])

        assert "schedules" not in snapshot.components

    async def test_it_records_a_failed_schedule_listing(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                success=False,
                action_type="schedule.List",
                device_ip="192.168.1.100",
                message="failed",
                error="timeout",
            )
        )

        snapshot = await use_case.capture("192.168.1.100", _status(), ["schedules"])

        assert snapshot.components["schedules"].success is False
        assert snapshot.components["schedules"].error == "timeout"
