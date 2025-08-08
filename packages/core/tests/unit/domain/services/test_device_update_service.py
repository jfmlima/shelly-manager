from unittest.mock import AsyncMock

import pytest
from core.domain.entities.exceptions import DeviceValidationError
from core.domain.entities.shelly_device import ShellyDevice
from core.domain.enums.enums import DeviceStatus, UpdateChannel
from core.domain.services.device_update_service import DeviceUpdateService
from core.domain.value_objects.action_result import ActionResult


class TestDeviceUpdateService:

    @pytest.fixture
    def service(self, mock_device_gateway):
        return DeviceUpdateService(device_gateway=mock_device_gateway)

    async def test_it_updates_device_successfully(self, service, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        action_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Update successful",
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result = await service.update_device(device_ip)

        assert result is True
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "stable"}
        )

    async def test_it_updates_device_with_beta_channel(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        action_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Beta update successful",
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result = await service.update_device(device_ip, UpdateChannel.BETA)

        assert result is True
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "beta"}
        )

    async def test_it_forces_update_when_no_update_available(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.14.0",
            has_update=False,
        )
        action_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Forced update successful",
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result = await service.update_device(device_ip, force=True)

        assert result is True

    async def test_it_raises_error_when_device_not_found(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        with pytest.raises(
            DeviceValidationError, match="Device 192.168.1.100 not found"
        ):
            await service.update_device(device_ip)

        mock_device_gateway.execute_action.assert_not_called()

    async def test_it_raises_error_when_no_update_available_and_not_forced(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.14.0",
            has_update=False,
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)

        with pytest.raises(DeviceValidationError, match="has no available updates"):
            await service.update_device(device_ip)

        mock_device_gateway.execute_action.assert_not_called()

    async def test_it_raises_error_when_device_status_invalid_for_update(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.UNREACHABLE,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)

        with pytest.raises(
            DeviceValidationError, match="is not in valid state for update"
        ):
            await service.update_device(device_ip)

        mock_device_gateway.execute_action.assert_not_called()

    async def test_it_raises_error_when_device_requires_auth(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.AUTH_REQUIRED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)

        with pytest.raises(
            DeviceValidationError, match="is not in valid state for update"
        ):
            await service.update_device(device_ip)

        mock_device_gateway.execute_action.assert_not_called()

    async def test_it_returns_false_when_action_fails(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        action_result = ActionResult(
            success=False,
            action_type="update",
            device_ip=device_ip,
            message="Update failed",
            error="Device busy",
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result = await service.update_device(device_ip)

        assert result is False

    async def test_it_uses_stable_channel_by_default(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        action_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Update successful",
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result = await service.update_device(device_ip)

        assert result is True
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "stable"}
        )

    async def test_it_handles_device_with_update_available(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        action_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Update successful",
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result = await service.update_device(device_ip, force=False)

        assert result is True

    async def test_it_propagates_gateway_exceptions(self, service, mock_device_gateway):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_status = AsyncMock(
            side_effect=Exception("Gateway error")
        )

        with pytest.raises(Exception, match="Gateway error"):
            await service.update_device(device_ip)

    async def test_it_validates_all_update_channels(self, service, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        action_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Update successful",
        )
        mock_device_gateway.get_device_status = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result_stable = await service.update_device(device_ip, UpdateChannel.STABLE)
        result_beta = await service.update_device(device_ip, UpdateChannel.BETA)

        assert result_stable is True
        assert result_beta is True
        assert mock_device_gateway.execute_action.call_count == 2
