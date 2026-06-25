from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from core.gateways.network.legacy_http_client import LegacyHttpClient


def _ok_response(data) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = data
    return resp


class TestLegacyHttpClient:

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        session.get = AsyncMock()
        session.aclose = AsyncMock()
        return session

    @pytest.fixture
    def client(self, mock_session):
        return LegacyHttpClient(session=mock_session, timeout=1.0)

    async def test_it_creates_client_with_custom_session(self, mock_session):
        client = LegacyHttpClient(session=mock_session, timeout=2.0)

        assert client._session is mock_session
        assert client.timeout == 2.0

    async def test_it_creates_client_with_default_session(self):
        client = LegacyHttpClient(timeout=3.0)

        assert isinstance(client._session, httpx.AsyncClient)
        assert client.timeout == 3.0

    async def test_it_fetches_json_successfully(self, client, mock_session):
        mock_session.get.return_value = _ok_response({"key": "value"})

        result = await client.fetch_json("192.168.1.100", "status")

        assert result == {"key": "value"}
        mock_session.get.assert_awaited_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "http://192.168.1.100/status"

    async def test_it_caps_connect_timeout(self, client, mock_session):
        mock_session.get.return_value = _ok_response({})

        await client.fetch_json("192.168.1.100", "status", timeout=5.0)

        timeout_arg = mock_session.get.call_args[1]["timeout"]
        assert isinstance(timeout_arg, httpx.Timeout)
        assert timeout_arg.read == 5.0
        assert timeout_arg.connect == 2.0

    async def test_it_handles_http_error_in_fetch_json(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Client Error", request=MagicMock(), response=MagicMock()
        )
        mock_session.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await client.fetch_json("192.168.1.100", "status")

    async def test_it_handles_non_dict_json_response(self, client, mock_session):
        mock_session.get.return_value = _ok_response(["list", "is", "not", "dict"])

        with pytest.raises(ValueError, match="did not return JSON object"):
            await client.fetch_json("192.168.1.100", "status")

    async def test_it_fetches_json_optional_success(self, client, mock_session):
        mock_session.get.return_value = _ok_response({"key": "value"})

        result = await client.fetch_json_optional("192.168.1.100", "settings")

        assert result == {"key": "value"}

    async def test_it_fetches_json_optional_failure(self, client, mock_session):
        mock_session.get.side_effect = httpx.ConnectError("boom")

        result = await client.fetch_json_optional("192.168.1.100", "settings")

        assert result == {}

    async def test_it_gets_with_params_successfully(self, client, mock_session):
        mock_session.get.return_value = _ok_response({"success": True})

        params = {"turn": "on"}
        result = await client.get_with_params("192.168.1.100", "relay/0", params)

        assert result == {"success": True}
        mock_session.get.assert_awaited_once()
        call_args = mock_session.get.call_args
        assert call_args[1]["params"] == params

    async def test_it_handles_value_error_in_get_with_params(
        self, client, mock_session
    ):
        mock_response = _ok_response("not a dict")
        mock_response.text = "raw response text"
        mock_session.get.return_value = mock_response

        result = await client.get_with_params("192.168.1.100", "relay/0", {})

        assert result == {"response": "raw response text"}

    async def test_it_closes_session(self, client, mock_session):
        await client.close()
        mock_session.aclose.assert_awaited_once()
