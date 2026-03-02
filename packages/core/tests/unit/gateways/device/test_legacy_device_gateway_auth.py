from unittest.mock import AsyncMock, MagicMock

import pytest
import requests
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

    async def test_ensure_mac_fetches_from_shelly(self, gateway, mock_http_client):
        mock_http_client.fetch_json.return_value = {"mac": "AA:BB:CC:DD:EE:FF"}

        mac = await gateway._ensure_mac("192.168.1.100")

        assert mac == "AABBCCDDEEFF"
        mock_http_client.fetch_json.assert_called_once_with("192.168.1.100", "shelly")

    async def test_ensure_mac_caches_result(self, gateway, mock_http_client):
        mock_http_client.fetch_json.return_value = {"mac": "AABBCCDDEEFF"}

        await gateway._ensure_mac("192.168.1.100")
        mac = await gateway._ensure_mac("192.168.1.100")

        assert mac == "AABBCCDDEEFF"
        assert mock_http_client.fetch_json.call_count == 1

    async def test_ensure_mac_returns_none_on_failure(self, gateway, mock_http_client):
        mock_http_client.fetch_json.side_effect = Exception("timeout")

        mac = await gateway._ensure_mac("192.168.1.100")

        assert mac is None

    async def test_ensure_mac_returns_none_when_no_mac(self, gateway, mock_http_client):
        mock_http_client.fetch_json.return_value = {"type": "SHSW-1"}

        mac = await gateway._ensure_mac("192.168.1.100")

        assert mac is None

    # --- _resolve_auth ---

    async def test_resolve_auth_returns_credentials(
        self, gateway, mock_http_client, mock_auth_service, sample_credential
    ):
        mock_http_client.fetch_json.return_value = {"mac": "AABBCCDDEEFF"}
        mock_auth_service.resolve_credentials.return_value = sample_credential

        auth = await gateway._resolve_auth("192.168.1.100")

        assert auth == ("admin", "secret")
        mock_auth_service.resolve_credentials.assert_called_once_with("AABBCCDDEEFF")

    async def test_resolve_auth_caches_credentials(
        self, gateway, mock_http_client, mock_auth_service, sample_credential
    ):
        mock_http_client.fetch_json.return_value = {"mac": "AABBCCDDEEFF"}
        mock_auth_service.resolve_credentials.return_value = sample_credential

        await gateway._resolve_auth("192.168.1.100")
        auth = await gateway._resolve_auth("192.168.1.100")

        assert auth == ("admin", "secret")
        assert mock_auth_service.resolve_credentials.call_count == 1

    async def test_resolve_auth_returns_none_without_service(
        self, gateway_no_auth, mock_http_client
    ):
        auth = await gateway_no_auth._resolve_auth("192.168.1.100")

        assert auth is None

    async def test_resolve_auth_returns_none_when_no_credential(
        self, gateway, mock_http_client, mock_auth_service
    ):
        mock_http_client.fetch_json.return_value = {"mac": "AABBCCDDEEFF"}
        mock_auth_service.resolve_credentials.return_value = None

        auth = await gateway._resolve_auth("192.168.1.100")

        assert auth is None

    # --- _fetch_with_auth ---

    async def test_fetch_with_auth_succeeds_without_401(
        self, gateway, mock_http_client
    ):
        mock_http_client.fetch_json.return_value = {"ok": True}

        result = await gateway._fetch_with_auth("192.168.1.100", "status")

        assert result == {"ok": True}
        mock_http_client.fetch_json.assert_called_once_with("192.168.1.100", "status")

    async def test_fetch_with_auth_retries_on_401(
        self, gateway, mock_http_client, mock_auth_service, sample_credential
    ):
        # First call raises 401, second succeeds with auth
        response_401 = MagicMock()
        response_401.status_code = 401
        http_error = requests.exceptions.HTTPError(response=response_401)

        mock_http_client.fetch_json.side_effect = [
            http_error,
            {"status": "ok"},
        ]
        # Pre-populate MAC cache
        gateway._ip_to_mac["192.168.1.100"] = "AABBCCDDEEFF"
        mock_auth_service.resolve_credentials.return_value = sample_credential

        result = await gateway._fetch_with_auth("192.168.1.100", "status")

        assert result == {"status": "ok"}
        assert mock_http_client.fetch_json.call_count == 2
        second_call = mock_http_client.fetch_json.call_args_list[1]
        assert second_call[1]["auth"] == ("admin", "secret")

    async def test_fetch_with_auth_raises_auth_error_when_no_credentials(
        self, gateway, mock_http_client, mock_auth_service
    ):
        response_401 = MagicMock()
        response_401.status_code = 401
        http_error = requests.exceptions.HTTPError(response=response_401)
        mock_http_client.fetch_json.side_effect = http_error
        mock_auth_service.resolve_credentials.return_value = None
        gateway._ip_to_mac["192.168.1.100"] = "AABBCCDDEEFF"

        with pytest.raises(DeviceAuthenticationError):
            await gateway._fetch_with_auth("192.168.1.100", "status")

    async def test_fetch_with_auth_re_raises_non_401_errors(
        self, gateway, mock_http_client
    ):
        response_500 = MagicMock()
        response_500.status_code = 500
        http_error = requests.exceptions.HTTPError(response=response_500)
        mock_http_client.fetch_json.side_effect = http_error

        with pytest.raises(requests.exceptions.HTTPError):
            await gateway._fetch_with_auth("192.168.1.100", "status")

    # --- discover_device with auth ---

    async def test_discover_detects_auth_and_fetches_with_credentials(
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

    async def test_discover_no_auth_when_not_required(
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

    async def test_get_device_status_retries_on_401(
        self,
        gateway,
        mock_http_client,
        mock_mapper,
        mock_auth_service,
        sample_credential,
    ):
        device_info = {"mac": "AABBCCDDEEFF", "type": "SHSW-1"}

        response_401 = MagicMock()
        response_401.status_code = 401
        http_error = requests.exceptions.HTTPError(response=response_401)

        # fetch_json: first call is /shelly (ok), second is status (401 via _fetch_with_auth),
        # third is status retry with auth (ok)
        mock_http_client.fetch_json.side_effect = [
            device_info,
            http_error,
            {"relays": []},
        ]
        mock_http_client.fetch_json_optional.return_value = {}
        mock_auth_service.resolve_credentials.return_value = sample_credential
        mock_mapper.map.return_value = []

        status = await gateway.get_device_status("192.168.1.100")

        assert status is not None

    async def test_get_device_status_returns_none_on_auth_failure(
        self,
        gateway,
        mock_http_client,
        mock_auth_service,
    ):
        device_info = {"mac": "AABBCCDDEEFF", "type": "SHSW-1"}

        response_401 = MagicMock()
        response_401.status_code = 401
        http_error = requests.exceptions.HTTPError(response=response_401)

        mock_http_client.fetch_json.side_effect = [device_info, http_error]
        mock_auth_service.resolve_credentials.return_value = None
        gateway._ip_to_mac["192.168.1.100"] = "AABBCCDDEEFF"

        status = await gateway.get_device_status("192.168.1.100")

        assert status is None

    # --- execute_action with auth ---

    async def test_execute_action_sends_auth(
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

    async def test_execute_action_no_auth_without_service(
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

    async def test_invalidate_credential_cache(self, gateway):
        gateway._basic_auth_cache["AABBCCDDEEFF"] = ("admin", "old_pass")

        gateway.invalidate_credential_cache("AA:BB:CC:DD:EE:FF")

        assert "AABBCCDDEEFF" not in gateway._basic_auth_cache

    async def test_invalidate_credential_cache_noop_for_unknown(self, gateway):
        # Should not raise
        gateway.invalidate_credential_cache("FFFFFFFFFFFF")
