from unittest.mock import AsyncMock

import pytest
from core.domain.enums.enums import UpdateChannel
from core.domain.value_objects.action_result import ActionResult
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase


class TestUpdateDeviceFirmwareUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return UpdateDeviceFirmwareUseCase(device_gateway=mock_device_gateway)

    async def test_it_updates_firmware_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Firmware update started successfully",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(device_ip)

        assert result.success is True
        assert result.action_type == "update"
        assert result.device_ip == device_ip
        assert result.message == "Firmware update started successfully"
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "stable"}
        )

    async def test_it_updates_firmware_with_beta_channel(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Beta firmware update started",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(device_ip, UpdateChannel.BETA)

        assert result.success is True
        assert result.message == "Beta firmware update started"
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "beta"}
        )

    async def test_it_handles_update_failure(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=False,
            action_type="update",
            device_ip=device_ip,
            message="Firmware update failed",
            error="Device already has latest firmware",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(device_ip)

        assert result.success is False
        assert result.action_type == "update"
        assert result.error == "Device already has latest firmware"
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "stable"}
        )

    async def test_it_passes_additional_parameters(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        additional_params = {"force": True, "timeout": 300}
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Forced firmware update started",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(
            device_ip, UpdateChannel.STABLE, **additional_params
        )

        assert result.success is True
        assert result.message == "Forced firmware update started"
        expected_params = {"channel": "stable", "force": True, "timeout": 300}
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", expected_params
        )

    async def test_it_defaults_to_stable_channel(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Firmware update started",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(device_ip)

        assert result.success is True
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "stable"}
        )

    async def test_it_handles_auth_required_device(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=False,
            action_type="update",
            device_ip=device_ip,
            message="Authentication required",
            error="Device requires username and password",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(device_ip)

        assert result.success is False
        assert result.error == "Device requires username and password"

    async def test_it_handles_offline_device(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=False,
            action_type="update",
            device_ip=device_ip,
            message="Device is offline",
            error="Connection timeout",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(device_ip)

        assert result.success is False
        assert result.message == "Device is offline"
        assert result.error == "Connection timeout"

    async def test_it_propagates_network_errors(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        mock_device_gateway.execute_action = AsyncMock(
            side_effect=ConnectionError("Network unreachable")
        )

        with pytest.raises(ConnectionError, match="Network unreachable"):
            await use_case.execute(device_ip)

    async def test_it_updates_multiple_devices_in_bulk(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.100",
                message="Update successful",
            ),
            ActionResult(
                success=False,
                action_type="update",
                device_ip="192.168.1.101",
                message="Update failed",
                error="Already latest version",
            ),
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.102",
                message="Update successful",
            ),
        ]
        mock_device_gateway.execute_action = AsyncMock(side_effect=expected_results)

        results = await use_case.execute_bulk(device_ips)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert mock_device_gateway.execute_action.call_count == 3

    async def test_it_updates_bulk_with_beta_channel(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.100",
                message="Beta update successful",
            ),
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.101",
                message="Beta update successful",
            ),
        ]
        mock_device_gateway.execute_action = AsyncMock(side_effect=expected_results)

        results = await use_case.execute_bulk(device_ips, UpdateChannel.BETA)

        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_device_gateway.execute_action.call_count == 2

    async def test_it_handles_bulk_update_with_additional_params(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        additional_params = {"force": True, "timeout": 600}
        expected_results = [
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.100",
                message="Forced update successful",
            )
        ]
        mock_device_gateway.execute_action = AsyncMock(side_effect=expected_results)

        results = await use_case.execute_bulk(
            device_ips, UpdateChannel.STABLE, **additional_params
        )

        assert len(results) == 1
        assert results[0].success is True
        assert mock_device_gateway.execute_action.call_count == 1

    async def test_it_includes_update_response_data(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Firmware update completed",
            data={
                "old_version": "1.13.0",
                "new_version": "1.14.0",
                "update_duration": 120,
                "device_type": "SHPM-1",
            },
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(device_ip)

        assert result.success is True
        assert result.data is not None
        assert result.data["old_version"] == "1.13.0"
        assert result.data["new_version"] == "1.14.0"
        assert result.data["update_duration"] == 120
