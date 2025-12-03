from unittest.mock import AsyncMock, MagicMock

import pytest
from core.domain.entities.device_status import DeviceStatus
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status
from core.gateways.device.legacy_component_mapper import LegacyComponentMapper
from core.gateways.device.legacy_device_gateway import LegacyDeviceGateway
from core.gateways.network.legacy_http_client import LegacyHttpClient


class TestLegacyDeviceGateway:

    @pytest.fixture
    def mock_http_client(self):
        return AsyncMock(spec=LegacyHttpClient)

    @pytest.fixture
    def mock_mapper(self):
        return MagicMock(spec=LegacyComponentMapper)

    @pytest.fixture
    def gateway(self, mock_http_client, mock_mapper):
        return LegacyDeviceGateway(
            http_client=mock_http_client, component_mapper=mock_mapper
        )

    @pytest.fixture
    def sample_device_info(self):
        return {
            "id": "shelly1-123456",
            "model": "SHSW-1",
            "mac": "AABBCCDDEEFF",
            "fw": "20230913-112003/v1.14.0-gCB16476",
            "type": "SHSW-1",
            "name": "Living Room Light",
        }

    @pytest.fixture
    def sample_status_data(self):
        return {
            "wifi_sta": {"connected": True, "ip": "192.168.1.100"},
            "has_update": False,
            "relays": [{"ison": False}],
        }

    @pytest.fixture
    def sample_settings_data(self):
        return {
            "device": {"name": "Custom Name"},
            "cfg_rev": 10,
        }

    async def test_it_discovers_device_successfully(
        self,
        gateway,
        mock_http_client,
        sample_device_info,
        sample_status_data,
        sample_settings_data,
    ):
        mock_http_client.fetch_json.return_value = sample_device_info
        mock_http_client.fetch_json_optional.side_effect = [
            sample_status_data,
            sample_settings_data,
        ]

        device = await gateway.discover_device("192.168.1.100")

        assert isinstance(device, DiscoveredDevice)
        assert device.ip == "192.168.1.100"
        assert device.device_id == "shelly1-123456"
        assert device.device_name == "Custom Name"
        assert device.status == Status.NO_UPDATE_NEEDED
        assert device.has_update is False

    async def test_it_handles_discovery_failure(self, gateway, mock_http_client):
        mock_http_client.fetch_json.side_effect = Exception("Connection error")

        device = await gateway.discover_device("192.168.1.100")

        assert device is None

    async def test_it_detects_update_available(
        self, gateway, mock_http_client, sample_device_info
    ):
        mock_http_client.fetch_json.return_value = sample_device_info
        mock_http_client.fetch_json_optional.side_effect = [
            {"has_update": True},
            {},
        ]

        device = await gateway.discover_device("192.168.1.100")

        assert device.status == Status.UPDATE_AVAILABLE
        assert device.has_update is True

    async def test_it_gets_device_status_successfully(
        self,
        gateway,
        mock_http_client,
        mock_mapper,
        sample_device_info,
        sample_status_data,
        sample_settings_data,
    ):
        mock_http_client.fetch_json.side_effect = [
            sample_device_info,
            sample_status_data,
        ]
        mock_http_client.fetch_json_optional.return_value = sample_settings_data

        mock_mapper.map.return_value = [{"key": "switch:0", "type": "switch"}]

        status = await gateway.get_device_status("192.168.1.100")

        assert isinstance(status, DeviceStatus)
        assert status.device_ip == "192.168.1.100"
        assert len(status.components) == 1
        mock_mapper.map.assert_called_once_with(
            sample_device_info, sample_status_data, sample_settings_data
        )

    async def test_it_handles_status_retrieval_failure(self, gateway, mock_http_client):
        mock_http_client.fetch_json.side_effect = Exception("Network error")

        status = await gateway.get_device_status("192.168.1.100")

        assert status is None

    async def test_it_executes_legacy_action_successfully(
        self, gateway, mock_http_client
    ):
        mock_http_client.get_with_params.return_value = {"ison": True}

        result = await gateway.execute_action(
            "192.168.1.100", "switch:0", "Legacy.TurnOn", {}
        )

        assert result.success is True
        assert result.data == {"ison": True}
        mock_http_client.get_with_params.assert_called_once_with(
            "192.168.1.100", "relay/0", {"turn": "on"}
        )

    async def test_it_handles_unsupported_legacy_action(self, gateway):
        result = await gateway.execute_action(
            "192.168.1.100", "switch:0", "Legacy.InvalidAction", {}
        )

        assert result.success is False
        assert result.error == "Unsupported legacy action"

    async def test_it_handles_action_execution_failure(self, gateway, mock_http_client):
        mock_http_client.get_with_params.side_effect = Exception("Action failed")

        result = await gateway.execute_action(
            "192.168.1.100", "switch:0", "Legacy.TurnOn", {}
        )

        assert result.success is False
        assert "Action failed" in result.error

    async def test_it_derives_device_name_priority(
        self, gateway, mock_http_client, sample_device_info
    ):
        # 1. Settings name (highest priority)
        mock_http_client.fetch_json.return_value = sample_device_info
        mock_http_client.fetch_json_optional.side_effect = [
            {},
            {"name": "Settings Name", "device": {"name": "Device Name"}},
        ]
        device = await gateway.discover_device("192.168.1.100")
        assert device.device_name == "Settings Name"

        # 2. Device settings name
        mock_http_client.fetch_json_optional.side_effect = [
            {},
            {"device": {"name": "Device Name"}},
        ]
        device = await gateway.discover_device("192.168.1.100")
        assert device.device_name == "Device Name"

        # 3. Info name
        mock_http_client.fetch_json_optional.side_effect = [{}, {}]
        device = await gateway.discover_device("192.168.1.100")
        assert device.device_name == "Living Room Light"

        # 4. Device ID (fallback)
        sample_device_info["name"] = None
        mock_http_client.fetch_json.return_value = sample_device_info
        mock_http_client.fetch_json_optional.side_effect = [{}, {}]
        device = await gateway.discover_device("192.168.1.100")
        assert device.device_name == "shelly1-123456"
