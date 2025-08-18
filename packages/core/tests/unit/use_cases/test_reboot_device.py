from unittest.mock import AsyncMock

import pytest
from core.domain.value_objects.reboot_device_request import RebootDeviceRequest
from core.domain.value_objects.action_result import ActionResult
from core.use_cases.reboot_device import RebootDeviceUseCase


class TestRebootDeviceUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return RebootDeviceUseCase(device_gateway=mock_device_gateway)

    async def test_it_reboots_device_successfully(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=True,
            action_type="reboot",
            device_ip=device_ip,
            message="Device rebooted successfully",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(RebootDeviceRequest(device_ip=device_ip))

        assert result.success is True
        assert result.action_type == "reboot"
        assert result.device_ip == device_ip
        assert result.message == "Device rebooted successfully"
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "reboot", {}
        )

    async def test_it_handles_reboot_failure(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=False,
            action_type="reboot",
            device_ip=device_ip,
            message="Reboot failed",
            error="Device unreachable",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(RebootDeviceRequest(device_ip=device_ip))

        assert result.success is False
        assert result.action_type == "reboot"
        assert result.device_ip == device_ip
        assert result.message == "Reboot failed"
        assert result.error == "Device unreachable"
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "reboot", {}
        )

    async def test_it_passes_additional_parameters(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        additional_params = {"delay": 5, "force": True}
        expected_result = ActionResult(
            success=True,
            action_type="reboot",
            device_ip=device_ip,
            message="Device reboot scheduled",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(RebootDeviceRequest(device_ip=device_ip, delay=5, force=True))

        assert result.success is True
        assert result.message == "Device reboot scheduled"
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "reboot", additional_params
        )

    async def test_it_handles_auth_required(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=False,
            action_type="reboot",
            device_ip=device_ip,
            message="Authentication required",
            error="Device requires username and password",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(RebootDeviceRequest(device_ip=device_ip))

        assert result.success is False
        assert result.error == "Device requires username and password"
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "reboot", {}
        )

    async def test_it_handles_offline_device(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=False,
            action_type="reboot",
            device_ip=device_ip,
            message="Device is offline",
            error="Connection timeout after 30 seconds",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(RebootDeviceRequest(device_ip=device_ip))

        assert result.success is False
        assert result.message == "Device is offline"
        assert "timeout" in result.error
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "reboot", {}
        )

    async def test_it_propagates_network_errors(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        mock_device_gateway.execute_action = AsyncMock(
            side_effect=ConnectionError("Network unreachable")
        )

        with pytest.raises(ConnectionError, match="Network unreachable"):
            await use_case.execute(RebootDeviceRequest(device_ip=device_ip))

    async def test_it_handles_credentials(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        auth_params = {"username": "admin", "password": "password123"}
        expected_result = ActionResult(
            success=True,
            action_type="reboot",
            device_ip=device_ip,
            message="Device rebooted successfully with authentication",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(RebootDeviceRequest(device_ip=device_ip, username="admin", password="password123"))

        assert result.success is True
        assert "authentication" in result.message
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "reboot", auth_params
        )

    async def test_it_handles_custom_timeout(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        timeout_params = {"timeout": 10}
        expected_result = ActionResult(
            success=True,
            action_type="reboot",
            device_ip=device_ip,
            message="Device rebooted successfully",
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(RebootDeviceRequest(device_ip=device_ip, timeout=10))

        assert result.success is True
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "reboot", timeout_params
        )

    async def test_it_propagates_gateway_exceptions(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.execute_action = AsyncMock(
            side_effect=Exception("Internal gateway error")
        )

        with pytest.raises(Exception, match="Internal gateway error"):
            await use_case.execute(RebootDeviceRequest(device_ip=device_ip))

    async def test_it_includes_response_data(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        expected_result = ActionResult(
            success=True,
            action_type="reboot",
            device_ip=device_ip,
            message="Device rebooted successfully",
            data={
                "reboot_time": "2023-09-13T15:30:00Z",
                "uptime_before_reboot": 3600,
                "device_type": "SHPM-1",
            },
        )
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(RebootDeviceRequest(device_ip=device_ip))

        assert result.success is True
        assert result.data is not None
        assert "reboot_time" in result.data
        assert "uptime_before_reboot" in result.data
        assert result.data["device_type"] == "SHPM-1"
