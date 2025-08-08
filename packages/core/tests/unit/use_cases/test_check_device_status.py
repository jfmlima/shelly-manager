from unittest.mock import AsyncMock

import pytest
from core.domain.entities.shelly_device import ShellyDevice
from core.domain.enums.enums import DeviceStatus
from core.use_cases.check_device_status import CheckDeviceStatusUseCase


class TestCheckDeviceStatusUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return CheckDeviceStatusUseCase(device_gateway=mock_device_gateway)

    async def test_it_returns_device_status_with_updates(
        self, use_case, mock_device_gateway, sample_shelly_device
    ):
        device_ip = "192.168.1.100"
        sample_shelly_device.has_update = True
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=sample_shelly_device
        )

        result = await use_case.execute(device_ip, include_updates=True)

        assert result is not None
        assert result.ip == device_ip
        assert result.status == DeviceStatus.DETECTED
        assert result.has_update is True
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip, True)

    async def test_it_returns_device_status_without_updates(
        self, use_case, mock_device_gateway, sample_shelly_device
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=sample_shelly_device
        )

        result = await use_case.execute(device_ip, include_updates=False)

        assert result is not None
        assert result.ip == device_ip
        assert result.status == DeviceStatus.DETECTED
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip, False)

    async def test_it_returns_none_when_device_not_found(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.999"
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        result = await use_case.execute(device_ip)

        assert result is None
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip, True)

    async def test_it_returns_offline_device_status(
        self, use_case, mock_device_gateway, sample_offline_device
    ):
        device_ip = "192.168.1.101"
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=sample_offline_device
        )

        result = await use_case.execute(device_ip)

        assert result is not None
        assert result.ip == device_ip
        assert result.status == DeviceStatus.UNREACHABLE
        assert result.error_message == "Connection timeout"
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip, True)

    async def test_it_returns_auth_required_device_status(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.102"
        auth_required_device = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.AUTH_REQUIRED,
            auth_required=True,
            device_id="shelly1pm-auth",
            device_type="SHPM-1",
        )
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=auth_required_device
        )

        result = await use_case.execute(device_ip)

        assert result is not None
        assert result.ip == device_ip
        assert result.status == DeviceStatus.AUTH_REQUIRED
        assert result.auth_required is True
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip, True)

    async def test_it_includes_response_time_information(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device_with_timing = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1pm-fast",
            device_type="SHPM-1",
            response_time=0.05,
        )
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=device_with_timing
        )

        result = await use_case.execute(device_ip)

        assert result is not None
        assert result.response_time == 0.05
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip, True)

    async def test_it_includes_firmware_information(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device_with_firmware = ShellyDevice(
            ip=device_ip,
            status=DeviceStatus.DETECTED,
            device_id="shelly1pm-fw",
            device_type="SHPM-1",
            firmware_version="20230913-114010/v1.14.0-gcb84623",
            has_update=True,
        )
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=device_with_firmware
        )

        result = await use_case.execute(device_ip, include_updates=True)

        assert result is not None
        assert result.firmware_version == "20230913-114010/v1.14.0-gcb84623"
        assert result.has_update is True
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip, True)

    async def test_it_defaults_include_updates_to_true(
        self, use_case, mock_device_gateway, sample_shelly_device
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=sample_shelly_device
        )

        result = await use_case.execute(device_ip)

        assert result is not None
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip, True)

    async def test_it_propagates_gateway_exceptions(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_status = AsyncMock(
            side_effect=Exception("Network connection failed")
        )

        with pytest.raises(Exception, match="Network connection failed"):
            await use_case.execute(device_ip)
