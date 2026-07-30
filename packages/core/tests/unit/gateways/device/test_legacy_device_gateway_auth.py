from unittest.mock import AsyncMock, MagicMock

import pytest
from core.domain.credentials import Credential
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.entities.exceptions import DeviceAuthenticationError
from core.gateways.device.legacy_component_mapper import LegacyComponentMapper
from core.gateways.device.legacy_device_gateway import LegacyDeviceGateway
from core.gateways.network.legacy_http_client import LegacyHttpClient
from core.services.auth_state_cache import AuthStateCache
from core.services.authentication_service import AuthenticationService


class TestLegacyDeviceGatewayAuth:

    @pytest.fixture
    def mock_http_client(self):
        return AsyncMock(spec=LegacyHttpClient)

    @pytest.fixture
    def mock_mapper(self):
        return MagicMock(spec=LegacyComponentMapper)

    @pytest.fixture
    def mock_auth_service(self):
        return AsyncMock(spec=AuthenticationService)

    @pytest.fixture
    def mock_auth_cache(self):
        return MagicMock(spec=AuthStateCache)

    @pytest.fixture
    def gateway(
        self, mock_http_client, mock_mapper, mock_auth_service, mock_auth_cache
    ):
        return LegacyDeviceGateway(
            http_client=mock_http_client,
            component_mapper=mock_mapper,
            authentication_service=mock_auth_service,
            auth_state_cache=mock_auth_cache,
        )

    @pytest.fixture
    def gateway_no_auth(self, mock_http_client, mock_mapper):
        return LegacyDeviceGateway(
            http_client=mock_http_client,
            component_mapper=mock_mapper,
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
            "auth": False,
        }

    @pytest.fixture
    def sample_device_info_auth(self, sample_device_info):
        return {**sample_device_info, "auth": True}

    @pytest.fixture
    def sample_credential(self):
        return Credential(mac="AABBCCDDEEFF", username="admin", password="secret")

    # --- _ensure_mac ---

    async def test_it_fetches_the_mac_from_shelly(self, gateway, mock_http_client):
        mock_http_client.fetch_json.return_value = {"mac": "AA:BB:CC:DD:EE:FF"}

        mac = await gateway._ensure_mac("192.168.1.100")

        assert mac == "AABBCCDDEEFF"
        mock_http_client.fetch_json.assert_called_once_with(
            "192.168.1.100", "shelly", timeout=None
        )

    async def test_it_caches_the_mac_it_fetched(self, gateway, mock_http_client):
        mock_http_client.fetch_json.return_value = {"mac": "AABBCCDDEEFF"}

        await gateway._ensure_mac("192.168.1.100")
        mac = await gateway._ensure_mac("192.168.1.100")

        assert mac == "AABBCCDDEEFF"
        assert mock_http_client.fetch_json.call_count == 1

    async def test_it_has_no_mac_when_the_fetch_fails(self, gateway, mock_http_client):
        mock_http_client.fetch_json.side_effect = Exception("timeout")

        mac = await gateway._ensure_mac("192.168.1.100")

        assert mac is None

    async def test_it_has_no_mac_when_the_device_reports_none(
        self, gateway, mock_http_client
    ):
        mock_http_client.fetch_json.return_value = {"type": "SHSW-1"}

        mac = await gateway._ensure_mac("192.168.1.100")

        assert mac is None

    # --- _resolve_auth ---

    async def test_it_resolves_credentials(
        self, gateway, mock_http_client, mock_auth_service, sample_credential
    ):
        mock_http_client.fetch_json.return_value = {"mac": "AABBCCDDEEFF"}
        mock_auth_service.resolve_credentials.return_value = sample_credential

        auth = await gateway._resolve_auth("192.168.1.100")

        assert auth == ("admin", "secret")
        mock_auth_service.resolve_credentials.assert_called_once_with("AABBCCDDEEFF")

    async def test_it_caches_resolved_credentials(
        self, gateway, mock_http_client, mock_auth_service, sample_credential
    ):
        mock_http_client.fetch_json.return_value = {"mac": "AABBCCDDEEFF"}
        mock_auth_service.resolve_credentials.return_value = sample_credential

        await gateway._resolve_auth("192.168.1.100")
        auth = await gateway._resolve_auth("192.168.1.100")

        assert auth == ("admin", "secret")
        assert mock_auth_service.resolve_credentials.call_count == 1

    async def test_it_resolves_nothing_without_an_authentication_service(
        self, gateway_no_auth, mock_http_client
    ):
        auth = await gateway_no_auth._resolve_auth("192.168.1.100")

        assert auth is None

    async def test_it_resolves_nothing_when_no_credential_is_stored(
        self, gateway, mock_http_client, mock_auth_service
    ):
        mock_http_client.fetch_json.return_value = {"mac": "AABBCCDDEEFF"}
        mock_auth_service.resolve_credentials.return_value = None

        auth = await gateway._resolve_auth("192.168.1.100")

        assert auth is None

    # --- discover_device with auth ---

    async def test_it_detects_auth_and_discovers_with_credentials(
        self,
        gateway,
        mock_http_client,
        mock_auth_service,
        mock_auth_cache,
        sample_device_info_auth,
        sample_credential,
    ):
        mock_http_client.fetch_json.return_value = sample_device_info_auth
        mock_http_client.fetch_json_optional.side_effect = [
            {"has_update": False},
            {"name": "My Device"},
        ]
        mock_auth_service.resolve_credentials.return_value = sample_credential

        device = await gateway.discover_device("192.168.1.100")

        assert isinstance(device, DiscoveredDevice)
        assert device.auth_required is True
        mock_auth_cache.mark_auth_required.assert_called_once_with("AABBCCDDEEFF")
        # status and settings should be called with auth
        for call in mock_http_client.fetch_json_optional.call_args_list:
            assert call[1].get("auth") == ("admin", "secret")

    async def test_it_discovers_without_auth_when_it_is_not_required(
        self,
        gateway,
        mock_http_client,
        mock_auth_cache,
        sample_device_info,
    ):
        mock_http_client.fetch_json.return_value = sample_device_info
        mock_http_client.fetch_json_optional.side_effect = [
            {"has_update": False},
            {},
        ]

        device = await gateway.discover_device("192.168.1.100")

        assert device.auth_required is False
        mock_auth_cache.mark_auth_required.assert_not_called()
        # status and settings called without auth
        for call in mock_http_client.fetch_json_optional.call_args_list:
            assert call[1].get("auth") is None

    # --- get_device_status with auth ---

    async def test_it_reads_status_with_proactive_auth(
        self,
        gateway,
        mock_http_client,
        mock_mapper,
        mock_auth_service,
        sample_credential,
    ):
        device_info = {"mac": "AABBCCDDEEFF", "type": "SHSW-1", "auth": True}

        mock_http_client.fetch_json.side_effect = [
            device_info,
            {"relays": []},
        ]
        mock_http_client.fetch_json_optional.return_value = {}
        mock_auth_service.resolve_credentials.return_value = sample_credential
        mock_mapper.map.return_value = []

        status = await gateway.get_device_status("192.168.1.100")

        assert status is not None
        # Second fetch_json call (status) should include auth
        status_call = mock_http_client.fetch_json.call_args_list[1]
        assert status_call[1].get("auth") == ("admin", "secret")

    async def test_it_raises_on_auth_failure_while_reading_status(
        self,
        gateway,
        mock_http_client,
        mock_auth_service,
    ):
        device_info = {"mac": "AABBCCDDEEFF", "type": "SHSW-1", "auth": True}

        mock_http_client.fetch_json.side_effect = [
            device_info,
            DeviceAuthenticationError("192.168.1.100"),
        ]
        mock_auth_service.resolve_credentials.return_value = None

        with pytest.raises(DeviceAuthenticationError):
            await gateway.get_device_status("192.168.1.100")

    # --- execute_action with auth ---

    async def test_it_sends_auth_with_an_action(
        self,
        gateway,
        mock_http_client,
        mock_auth_service,
        sample_credential,
    ):
        gateway._ip_to_mac["192.168.1.100"] = "AABBCCDDEEFF"
        mock_auth_service.resolve_credentials.return_value = sample_credential
        mock_http_client.get_with_params.return_value = {"ison": True}

        result = await gateway.execute_action(
            "192.168.1.100", "switch:0", "Legacy.TurnOn", {}
        )

        assert result.success is True
        call_kwargs = mock_http_client.get_with_params.call_args[1]
        assert call_kwargs.get("auth") == ("admin", "secret")

    async def test_it_sends_no_auth_with_an_action_without_a_service(
        self, gateway_no_auth, mock_http_client
    ):
        mock_http_client.get_with_params.return_value = {"ison": True}

        result = await gateway_no_auth.execute_action(
            "192.168.1.100", "switch:0", "Legacy.TurnOn", {}
        )

        assert result.success is True
        call_kwargs = mock_http_client.get_with_params.call_args[1]
        assert call_kwargs.get("auth") is None

    # --- invalidate_credential_cache ---

    async def test_it_invalidates_the_credential_cache(self, gateway):
        gateway._basic_auth_cache["AABBCCDDEEFF"] = ("admin", "old_pass")

        gateway.invalidate_credential_cache("AA:BB:CC:DD:EE:FF")

        assert "AABBCCDDEEFF" not in gateway._basic_auth_cache

    async def test_it_invalidates_nothing_for_an_unknown_device(self, gateway):
        # Should not raise
        gateway.invalidate_credential_cache("FFFFFFFFFFFF")
