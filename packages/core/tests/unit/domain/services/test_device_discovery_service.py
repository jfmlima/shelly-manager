from unittest.mock import AsyncMock

import pytest
from core.domain.entities.exceptions import DeviceValidationError
from core.domain.entities.shelly_device import ShellyDevice
from core.domain.enums.enums import DeviceStatus
from core.domain.services.device_discovery_service import DeviceDiscoveryService


class TestDeviceDiscoveryService:

    @pytest.fixture
    def service(self, mock_device_gateway):
        return DeviceDiscoveryService(device_gateway=mock_device_gateway)

    async def test_it_discovers_valid_device_successfully(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.14.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        result = await service.discover_device(device_ip)

        assert result is not None
        assert result.ip == device_ip
        assert result.status == DeviceStatus.DETECTED
        assert result.device_type == "SHSW-1"
        mock_device_gateway.discover_device.assert_called_once_with(device_ip, 3.0)

    async def test_it_returns_none_when_device_not_found(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        result = await service.discover_device(device_ip)

        assert result is None
        mock_device_gateway.discover_device.assert_called_once_with(device_ip, 3.0)

    async def test_it_applies_auth_required_status_rule(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.14.0",
            auth_required=True,
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        result = await service.discover_device(device_ip)

        assert result.status == DeviceStatus.AUTH_REQUIRED
        assert result.auth_required is True

    async def test_it_validates_device_type_presence(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type=None,
            firmware_version="1.14.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        with pytest.raises(DeviceValidationError, match="has no device type"):
            await service.discover_device(device_ip)

    async def test_it_validates_firmware_version_presence(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version=None,
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        with pytest.raises(DeviceValidationError, match="has no firmware version"):
            await service.discover_device(device_ip)

    async def test_it_uses_custom_timeout(self, service, mock_device_gateway):
        device_ip = "192.168.1.100"
        timeout = 5.0
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.14.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        result = await service.discover_device(device_ip, timeout)

        assert result is not None
        mock_device_gateway.discover_device.assert_called_once_with(device_ip, timeout)

    async def test_it_raises_validation_error_on_gateway_exception(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.discover_device = AsyncMock(
            side_effect=ConnectionError("Network error")
        )

        with pytest.raises(DeviceValidationError, match="Failed to discover device"):
            await service.discover_device(device_ip)

    async def test_it_wraps_gateway_exception_in_validation_error(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        original_error = Exception("Gateway internal error")
        mock_device_gateway.discover_device = AsyncMock(side_effect=original_error)

        with pytest.raises(DeviceValidationError) as exc_info:
            await service.discover_device(device_ip)

        assert exc_info.value.__cause__ is original_error
        assert "Gateway internal error" in str(exc_info.value)

    async def test_it_preserves_detected_status_when_no_auth_required(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.14.0",
            auth_required=False,
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        result = await service.discover_device(device_ip)

        assert result.status == DeviceStatus.DETECTED
        assert result.auth_required is False

    async def test_it_validates_device_with_minimal_required_fields(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="minimal-device",
            device_type="SHSW-1",
            firmware_version="1.0.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        result = await service.discover_device(device_ip)

        assert result is not None
        assert result.device_type == "SHSW-1"
        assert result.firmware_version == "1.0.0"

    async def test_it_validates_device_with_empty_device_type(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="",
            firmware_version="1.14.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        with pytest.raises(DeviceValidationError, match="has no device type"):
            await service.discover_device(device_ip)

    async def test_it_validates_device_with_empty_firmware_version(
        self, service, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        with pytest.raises(DeviceValidationError, match="has no firmware version"):
            await service.discover_device(device_ip)
