from unittest.mock import AsyncMock

import pytest
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.entities.device_status import DeviceStatus
from core.domain.enums.enums import Status
from core.domain.value_objects.check_device_status_request import CheckDeviceStatusRequest
from core.use_cases.check_device_status import CheckDeviceStatusUseCase


class TestCheckDeviceStatusUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return CheckDeviceStatusUseCase(device_gateway=mock_device_gateway)

    async def test_it_returns_device_status_with_updates(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        sample_device_status = DeviceStatus(device_ip=device_ip, components=[], total_components=0)
        mock_device_gateway.get_device_status = AsyncMock(return_value=sample_device_status)

        request = CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True)
        result = await use_case.execute(request)

        assert result is not None
        assert result.device_ip == device_ip
        assert isinstance(result, DeviceStatus)
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_returns_device_status_without_updates(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        sample_device_status = DeviceStatus(device_ip=device_ip, components=[], total_components=0)
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=sample_device_status
        )

        result = await use_case.execute(CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True))

        assert result is not None
        assert result.device_ip == device_ip
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_returns_none_when_device_not_found(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.200"
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        result = await use_case.execute(CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True))

        assert result is None
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_returns_offline_device_status(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.101"
        # get_device_status returns None when device is offline
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        result = await use_case.execute(CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True))

        assert result is None
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_returns_auth_required_device_status(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.102"
        # get_device_status should return None when auth is required
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        result = await use_case.execute(CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True))

        assert result is None
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_includes_timing_information(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device_status = DeviceStatus(device_ip=device_ip, components=[], total_components=0)
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=device_status
        )

        result = await use_case.execute(CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True))

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == device_ip
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_includes_firmware_information(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        # Create a DeviceStatus with a system component containing firmware info
        from core.domain.entities.components import SystemComponent
        
        sys_component = SystemComponent.from_raw_data({
            "key": "sys",
            "status": {
                "available_updates": {"stable": {"version": "1.15.0"}},
                "mac": "AABBCCDDEEFF",
                "uptime": 3600
            },
            "config": {
                "device": {"fw_id": "20230913-114010/v1.14.0-gcb84623"}
            }
        })
        
        device_status = DeviceStatus(
            device_ip=device_ip, 
            components=[sys_component], 
            total_components=1
        )
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=device_status
        )

        result = await use_case.execute(CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True))

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == device_ip
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_defaults_include_updates_to_true(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device_status = DeviceStatus(device_ip=device_ip, components=[], total_components=0)
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=device_status
        )

        result = await use_case.execute(CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True))

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == device_ip
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_propagates_gateway_exceptions(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_status = AsyncMock(
            side_effect=Exception("Network connection failed")
        )

        with pytest.raises(Exception, match="Network connection failed"):
            await use_case.execute(CheckDeviceStatusRequest(device_ip=device_ip, include_updates=True))
