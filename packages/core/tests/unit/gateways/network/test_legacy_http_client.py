from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests
from core.gateways.network.legacy_http_client import LegacyHttpClient


class TestLegacyHttpClient:

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=requests.Session)

    @pytest.fixture
    def client(self, mock_session):
        return LegacyHttpClient(session=mock_session, timeout=1.0)

    @pytest.fixture
    def client_with_default_session(self):
        return LegacyHttpClient()

    async def test_it_creates_client_with_custom_session(self, mock_session):
        client = LegacyHttpClient(session=mock_session, timeout=2.0)

        assert client._session is mock_session
        assert client.timeout == 2.0

    async def test_it_creates_client_with_default_session(self):
        client = LegacyHttpClient(timeout=3.0)

        assert isinstance(client._session, requests.Session)
        assert client.timeout == 3.0

    async def test_it_fetches_json_successfully(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_session.get.return_value = mock_response

        result = await client.fetch_json("192.168.1.100", "status")

        assert result == {"key": "value"}
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "http://192.168.1.100/status"

    async def test_it_handles_http_error_in_fetch_json(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Client Error"
        )
        mock_session.get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            await client.fetch_json("192.168.1.100", "status")

    async def test_it_handles_non_dict_json_response(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["list", "is", "not", "dict"]
        mock_session.get.return_value = mock_response

        with pytest.raises(ValueError, match="did not return JSON object"):
            await client.fetch_json("192.168.1.100", "status")

    async def test_it_fetches_json_optional_success(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_session.get.return_value = mock_response

        result = await client.fetch_json_optional("192.168.1.100", "settings")

        assert result == {"key": "value"}

    async def test_it_fetches_json_optional_failure(self, client, mock_session):
        mock_session.get.side_effect = requests.exceptions.ConnectionError

        result = await client.fetch_json_optional("192.168.1.100", "settings")

        assert result == {}

    async def test_it_gets_with_params_successfully(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_session.get.return_value = mock_response

        params = {"turn": "on"}
        result = await client.get_with_params("192.168.1.100", "relay/0", params)

        assert result == {"success": True}
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[1]["params"] == params

    async def test_it_handles_value_error_in_get_with_params(
        self, client, mock_session
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulate invalid JSON or non-dict response that raises ValueError in logic
        mock_response.json.return_value = "not a dict"
        mock_session.get.return_value = mock_response
        mock_response.text = "raw response text"

        result = await client.get_with_params("192.168.1.100", "relay/0", {})

        assert result == {"response": "raw response text"}

    async def test_it_closes_session(self, client, mock_session):
        await client.close()
        mock_session.close.assert_called_once()

    async def test_it_runs_in_executor(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.get.return_value = mock_response

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_executor = AsyncMock(return_value={})
            mock_loop.return_value.run_in_executor = mock_executor

            await client.fetch_json("192.168.1.100", "status")

            mock_executor.assert_called_once()
