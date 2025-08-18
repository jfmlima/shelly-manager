from unittest.mock import AsyncMock

import pytest
from core.domain.value_objects.device_configuration_request import DeviceConfigurationRequest
from core.use_cases.get_configuration import GetConfigurationUseCase


class TestGetConfigurationUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return GetConfigurationUseCase(device_gateway=mock_device_gateway)

    async def test_it_retrieves_configuration_successfully(
        self, use_case, mock_device_gateway, sample_device_config
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_config = AsyncMock(
            return_value=sample_device_config
        )

        result = await use_case.execute(DeviceConfigurationRequest(device_ip=device_ip))

        assert result == sample_device_config
        assert "wifi" in result
        assert "mqtt" in result
        assert result["name"] == "Test Device"
        mock_device_gateway.get_device_config.assert_called_once_with(device_ip)

    async def test_it_raises_error_when_device_not_found(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.200"
        mock_device_gateway.get_device_config = AsyncMock(return_value=None)

        with pytest.raises(
            ValueError,
            match="Could not retrieve configuration for device: 192.168.1.200",
        ):
            await use_case.execute(DeviceConfigurationRequest(device_ip=device_ip))

        mock_device_gateway.get_device_config.assert_called_once_with(device_ip)

    async def test_it_handles_empty_configuration(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        empty_config = {}
        mock_device_gateway.get_device_config = AsyncMock(return_value=empty_config)

        result = await use_case.execute(DeviceConfigurationRequest(device_ip=device_ip))

        assert result == empty_config
        mock_device_gateway.get_device_config.assert_called_once_with(device_ip)

    async def test_it_handles_complex_configuration(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        complex_config = {
            "wifi": {
                "sta": {
                    "ssid": "MyNetwork",
                    "pass": "password123",
                    "enable": True,
                    "ipv4method": "dhcp",
                },
                "ap": {"ssid": "shelly1pm-68A3", "enable": False},
            },
            "mqtt": {
                "enable": True,
                "server": "192.168.1.50:1883",
                "user": "mqtt_user",
                "id": "shelly1pm-001",
                "reconnect_timeout_max": 60.0,
                "reconnect_timeout_min": 2.0,
                "clean_session": True,
                "keep_alive": 60,
                "will_topic": "shellies/shelly1pm-001/online",
                "will_message": "false",
                "max_qos": 0,
                "retain": False,
                "update_period": 30,
            },
            "sntp": {"server": "time.google.com", "enable": True},
            "login": {"enabled": False, "unprotected": False, "username": "admin"},
            "pin_code": "",
            "name": "Living Room Switch",
            "fw": "20230913-114010/v1.14.0-gcb84623",
            "discoverable": True,
            "build_info": {
                "build_id": "20230913-114010/v1.14.0-gcb84623",
                "build_timestamp": "2023-09-13T11:40:10Z",
                "build_version": "1.0",
            },
            "cloud": {"enabled": True, "connected": True},
            "timezone": "America/New_York",
            "lat": 40.7128,
            "lng": -74.0060,
            "tzautodetect": True,
            "tz_utc_offset": -14400,
            "tz_dst": False,
            "tz_dst_auto": True,
            "time": "15:30",
        }
        mock_device_gateway.get_device_config = AsyncMock(return_value=complex_config)

        result = await use_case.execute(DeviceConfigurationRequest(device_ip=device_ip))

        assert result == complex_config
        assert result["wifi"]["sta"]["ssid"] == "MyNetwork"
        assert result["mqtt"]["enable"] is True
        assert result["name"] == "Living Room Switch"
        assert "build_info" in result
        mock_device_gateway.get_device_config.assert_called_once_with(device_ip)

    async def test_it_raises_error_for_auth_required_device(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_config = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Could not retrieve configuration"):
            await use_case.execute(DeviceConfigurationRequest(device_ip=device_ip))

    async def test_it_propagates_gateway_exceptions(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_config = AsyncMock(
            side_effect=Exception("Connection timeout")
        )

        with pytest.raises(Exception, match="Connection timeout"):
            await use_case.execute(DeviceConfigurationRequest(device_ip=device_ip))

        mock_device_gateway.get_device_config.assert_called_once_with(device_ip)

    async def test_it_handles_network_errors(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        mock_device_gateway.get_device_config = AsyncMock(
            side_effect=ConnectionError("Device unreachable")
        )

        with pytest.raises(ConnectionError, match="Device unreachable"):
            await use_case.execute(DeviceConfigurationRequest(device_ip=device_ip))

    async def test_it_handles_partial_configuration(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        partial_config = {"name": "Partial Device", "wifi": {"sta": {"enable": True}}}
        mock_device_gateway.get_device_config = AsyncMock(return_value=partial_config)

        result = await use_case.execute(DeviceConfigurationRequest(device_ip=device_ip))

        assert result == partial_config
        assert result["name"] == "Partial Device"
        assert "mqtt" not in result
        mock_device_gateway.get_device_config.assert_called_once_with(device_ip)
