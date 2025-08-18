from unittest.mock import AsyncMock

import pytest
from core.domain.value_objects.set_configuration_request import SetConfigurationRequest
from core.use_cases.set_configuration import SetConfigurationUseCase


class TestSetConfigurationUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return SetConfigurationUseCase(device_gateway=mock_device_gateway)

    async def test_it_updates_configuration_successfully(
        self, use_case, mock_device_gateway, sample_device_config
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.set_device_config = AsyncMock(return_value=True)

        result = await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=sample_device_config))

        assert result["success"] is True
        assert result["message"] == "Configuration updated successfully"
        mock_device_gateway.set_device_config.assert_called_once_with(
            device_ip, sample_device_config
        )

    async def test_it_handles_configuration_update_failure(
        self, use_case, mock_device_gateway, sample_device_config
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.set_device_config = AsyncMock(return_value=False)

        result = await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=sample_device_config))

        assert result["success"] is False
        assert result["message"] == "Failed to update configuration"
        mock_device_gateway.set_device_config.assert_called_once_with(
            device_ip, sample_device_config
        )

    async def test_it_validates_empty_configuration(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        empty_config = {}

        with pytest.raises(ValueError, match="Configuration data required"):
            await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=empty_config))

        mock_device_gateway.set_device_config.assert_not_called()

    async def test_it_validates_none_configuration(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        none_config = None

        # Pydantic will raise ValidationError when config is None since it's required
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="Input should be a valid dictionary"):
            SetConfigurationRequest(device_ip=device_ip, config=none_config)

        mock_device_gateway.set_device_config.assert_not_called()

    async def test_it_updates_wifi_configuration(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        wifi_config = {
            "wifi": {
                "sta": {
                    "ssid": "NewNetwork",
                    "pass": "newpassword123",
                    "enable": True,
                    "ipv4method": "static",
                    "ip": "192.168.1.150",
                    "netmask": "255.255.255.0",
                    "gateway": "192.168.1.1",
                    "dns": "8.8.8.8",
                }
            }
        }
        mock_device_gateway.set_device_config = AsyncMock(return_value=True)

        result = await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=wifi_config))

        assert result["success"] is True
        assert result["message"] == "Configuration updated successfully"
        mock_device_gateway.set_device_config.assert_called_once_with(
            device_ip, wifi_config
        )

    async def test_it_updates_mqtt_configuration(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        mqtt_config = {
            "mqtt": {
                "enable": True,
                "server": "mqtt.example.com:1883",
                "user": "mqtt_user",
                "pass": "mqtt_password",
                "id": "shelly1pm-001",
                "clean_session": True,
                "keep_alive": 60,
                "max_qos": 1,
                "retain": True,
                "update_period": 30,
            }
        }
        mock_device_gateway.set_device_config = AsyncMock(return_value=True)

        result = await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=mqtt_config))

        assert result["success"] is True
        mock_device_gateway.set_device_config.assert_called_once_with(
            device_ip, mqtt_config
        )

    async def test_it_updates_device_name(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        name_config = {"name": "Living Room Light Switch"}
        mock_device_gateway.set_device_config = AsyncMock(return_value=True)

        result = await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=name_config))

        assert result["success"] is True
        mock_device_gateway.set_device_config.assert_called_once_with(
            device_ip, name_config
        )

    async def test_it_updates_complex_configuration(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        complex_config = {
            "wifi": {"sta": {"ssid": "HomeNetwork", "enable": True}},
            "mqtt": {"enable": True, "server": "192.168.1.50:1883"},
            "name": "Updated Device Name",
            "sntp": {"server": "pool.ntp.org", "enable": True},
            "timezone": "America/New_York",
        }
        mock_device_gateway.set_device_config = AsyncMock(return_value=True)

        result = await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=complex_config))

        assert result["success"] is True
        mock_device_gateway.set_device_config.assert_called_once_with(
            device_ip, complex_config
        )

    async def test_it_propagates_gateway_exceptions(
        self, use_case, mock_device_gateway, sample_device_config
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.set_device_config = AsyncMock(
            side_effect=Exception("Device unreachable")
        )

        with pytest.raises(Exception, match="Device unreachable"):
            await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=sample_device_config))

    async def test_it_handles_network_timeout(
        self, use_case, mock_device_gateway, sample_device_config
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.set_device_config = AsyncMock(
            side_effect=ConnectionError("Connection timeout")
        )

        with pytest.raises(ConnectionError, match="Connection timeout"):
            await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=sample_device_config))

    async def test_it_handles_auth_required_scenario(
        self, use_case, mock_device_gateway, sample_device_config
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.set_device_config = AsyncMock(return_value=False)

        result = await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=sample_device_config))

        assert result["success"] is False
        assert result["message"] == "Failed to update configuration"

    async def test_it_updates_partial_configuration(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        partial_config = {"name": "New Device Name"}
        mock_device_gateway.set_device_config = AsyncMock(return_value=True)

        result = await use_case.execute(SetConfigurationRequest(device_ip=device_ip, config=partial_config))

        assert result["success"] is True
        assert result["message"] == "Configuration updated successfully"
        mock_device_gateway.set_device_config.assert_called_once_with(
            device_ip, partial_config
        )
