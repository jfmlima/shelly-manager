from unittest.mock import MagicMock

import pytest
import requests
from core.gateways.network.legacy_http_client import LegacyHttpClient


class TestLegacyHttpClientAuth:

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=requests.Session)

    @pytest.fixture
    def client(self, mock_session):
        return LegacyHttpClient(session=mock_session, timeout=1.0)

    def _mock_ok_response(self, data: dict) -> MagicMock:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = data
        return resp

    async def test_fetch_json_passes_auth_to_session(self, client, mock_session):
        mock_session.get.return_value = self._mock_ok_response({"ok": True})

        result = await client.fetch_json(
            "192.168.1.1", "status", auth=("admin", "secret")
        )

        assert result == {"ok": True}
        call_kwargs = mock_session.get.call_args[1]
        assert call_kwargs["auth"] == ("admin", "secret")

    async def test_fetch_json_passes_none_auth_by_default(self, client, mock_session):
        mock_session.get.return_value = self._mock_ok_response({"ok": True})

        await client.fetch_json("192.168.1.1", "status")

        call_kwargs = mock_session.get.call_args[1]
        assert call_kwargs["auth"] is None

    async def test_fetch_json_optional_passes_auth(self, client, mock_session):
        mock_session.get.return_value = self._mock_ok_response({"ok": True})

        result = await client.fetch_json_optional(
            "192.168.1.1", "settings", auth=("admin", "pw")
        )

        assert result == {"ok": True}
        call_kwargs = mock_session.get.call_args[1]
        assert call_kwargs["auth"] == ("admin", "pw")

    async def test_get_with_params_passes_auth(self, client, mock_session):
        mock_session.get.return_value = self._mock_ok_response({"ison": True})

        result = await client.get_with_params(
            "192.168.1.1", "relay/0", {"turn": "on"}, auth=("admin", "pass")
        )

        assert result == {"ison": True}
        call_kwargs = mock_session.get.call_args[1]
        assert call_kwargs["auth"] == ("admin", "pass")

    async def test_get_with_params_none_auth_by_default(self, client, mock_session):
        mock_session.get.return_value = self._mock_ok_response({"ison": True})

        await client.get_with_params("192.168.1.1", "relay/0", {"turn": "on"})

        call_kwargs = mock_session.get.call_args[1]
        assert call_kwargs["auth"] is None
