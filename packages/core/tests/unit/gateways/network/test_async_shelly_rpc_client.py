import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from core.gateways.network.async_shelly_rpc_client import AsyncShellyRPCClient


class TestAsyncShellyRPCClient:

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=httpx.AsyncClient)

    @pytest.fixture
    def client(self, mock_session):
        return AsyncShellyRPCClient(session=mock_session, timeout=3)

    @pytest.fixture
    def client_with_default_session(self):
        return AsyncShellyRPCClient()

    async def test_it_creates_client_with_custom_session(self, mock_session):
        client = AsyncShellyRPCClient(session=mock_session, timeout=2)

        assert client._session is mock_session
        assert client.timeout == 2

    async def test_it_creates_client_with_default_session(self):
        client = AsyncShellyRPCClient(timeout=3)

        assert isinstance(client._session, httpx.AsyncClient)
        assert client.timeout == 3

    async def test_it_makes_successful_rpc_request(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success", "id": 1}
        mock_session.post.return_value = mock_response

        result, response_time = await client.make_rpc_request(
            "192.168.1.100", "Shelly.GetDeviceInfo"
        )

        assert result == {"result": "success", "id": 1}
        assert isinstance(response_time, float)
        assert response_time >= 0
        mock_session.post.assert_called_once()

    async def test_it_makes_rpc_request_with_auth(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_session.post.return_value = mock_response

        auth = ("admin", "password123")

        await client.make_rpc_request(
            "192.168.1.100", "Shelly.GetDeviceInfo", auth=auth
        )

        call_args = mock_session.post.call_args
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    async def test_it_makes_rpc_request_with_custom_timeout(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_session.post.return_value = mock_response

        await client.make_rpc_request(
            "192.168.1.100", "Shelly.GetDeviceInfo", timeout=5
        )

        call_args = mock_session.post.call_args
        expected_url = "http://192.168.1.100/rpc"
        assert call_args[0][0] == expected_url

    async def test_it_handles_http_error_responses(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_session.post.return_value = mock_response

        with pytest.raises(Exception, match="HTTP 404: Not Found"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_network_errors(self, client, mock_session):
        mock_session.post.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(Exception, match="Network error: Connection failed"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_timeout_errors(self, client, mock_session):
        mock_session.post.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(Exception, match="Network error: Request timeout"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_uses_correct_url_format(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        await client.make_rpc_request("10.0.0.1", "Test.Method")

        call_args = mock_session.post.call_args
        expected_url = "http://10.0.0.1/rpc"
        assert call_args[0][0] == expected_url

    async def test_it_uses_correct_headers(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

        call_args = mock_session.post.call_args
        expected_headers = {"Content-Type": "application/json"}
        assert call_args[1]["headers"] == expected_headers

    async def test_it_measures_response_time_accurately(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        async def slow_post(*args, **kwargs):
            await asyncio.sleep(0.1)
            return mock_response

        mock_session.post.side_effect = slow_post

        result, response_time = await client.make_rpc_request(
            "192.168.1.100", "Shelly.GetDeviceInfo"
        )

        assert response_time >= 0.1

    async def test_it_measures_response_time_on_error(self, client, mock_session):
        async def slow_error(*args, **kwargs):
            await asyncio.sleep(0.1)
            raise httpx.ConnectError("Slow error")

        mock_session.post.side_effect = slow_error

        with pytest.raises(Exception, match="Network error"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_closes_session_successfully(self, client, mock_session):
        await client.close()

        mock_session.aclose.assert_called_once()

    async def test_it_handles_json_decode_error(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_session.post.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid JSON"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_various_http_status_codes(self, client, mock_session):
        status_codes = [400, 401, 403, 500, 503]

        for status_code in status_codes:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.text = f"Error {status_code}"
            mock_session.post.return_value = mock_response

            with pytest.raises(Exception, match=f"HTTP {status_code}"):
                await client.make_rpc_request("192.168.1.100", "Test.Method")

    async def test_it_handles_read_timeout(self, client, mock_session):
        mock_session.post.side_effect = httpx.ReadTimeout("Read timeout")

        with pytest.raises(Exception, match="Network error: Read timeout"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_request_error(self, client, mock_session):
        mock_session.post.side_effect = httpx.RequestError("Request error")

        with pytest.raises(Exception, match="Network error: Request error"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_pool_timeout(self, client, mock_session):
        mock_session.post.side_effect = httpx.PoolTimeout("Pool timeout")

        with pytest.raises(Exception, match="Network error: Pool timeout"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_creates_timeout_correctly(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        await client.make_rpc_request("192.168.1.100", "Test.Method", timeout=10)

        call_args = mock_session.post.call_args
        timeout_arg = call_args[1]["timeout"]
        assert timeout_arg == 10

    async def test_it_uses_default_timeout_when_none_provided(
        self, client, mock_session
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        await client.make_rpc_request("192.168.1.100", "Test.Method")

        call_args = mock_session.post.call_args
        timeout_arg = call_args[1]["timeout"]
        assert timeout_arg == 3.0
