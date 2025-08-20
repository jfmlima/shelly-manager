import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests
from core.gateways.network.shelly_rpc_client import ShellyRPCClient


class TestShellyRPCClient:

    @pytest.fixture
    def mock_session(self):
        return MagicMock(spec=requests.Session)

    @pytest.fixture
    def client(self, mock_session):
        return ShellyRPCClient(session=mock_session, timeout=1.0)

    @pytest.fixture
    def client_with_default_session(self):
        return ShellyRPCClient()

    async def test_it_creates_client_with_custom_session(self, mock_session):
        client = ShellyRPCClient(session=mock_session, timeout=2.0)

        assert client.session is mock_session
        assert client.timeout == 2.0

    async def test_it_creates_client_with_default_session(self):
        client = ShellyRPCClient(timeout=3.0)

        assert isinstance(client.session, requests.Session)
        assert client.timeout == 3.0

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
        assert call_args[1]["auth"] == auth

    async def test_it_makes_rpc_request_with_custom_timeout(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_session.post.return_value = mock_response

        await client.make_rpc_request(
            "192.168.1.100", "Shelly.GetDeviceInfo", timeout=5.0
        )

        call_args = mock_session.post.call_args
        expected_url = "http://192.168.1.100/rpc/Shelly.GetDeviceInfo"
        assert call_args[0][0] == expected_url

    async def test_it_handles_http_error_responses(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_session.post.return_value = mock_response

        with pytest.raises(Exception, match="HTTP 404: Not Found"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_network_errors(self, client, mock_session):
        mock_session.post.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        with pytest.raises(Exception, match="Network error: Connection failed"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_timeout_errors(self, client, mock_session):
        mock_session.post.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(Exception, match="Network error: Request timeout"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_uses_correct_url_format(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        await client.make_rpc_request("10.0.0.1", "Test.Method")

        call_args = mock_session.post.call_args
        expected_url = "http://10.0.0.1/rpc/Test.Method"
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

        def slow_post(*args, **kwargs):
            time.sleep(0.1)
            return mock_response

        mock_session.post.side_effect = slow_post

        result, response_time = await client.make_rpc_request(
            "192.168.1.100", "Shelly.GetDeviceInfo"
        )

        assert response_time >= 0.1

    async def test_it_measures_response_time_on_error(self, client, mock_session):
        def slow_error(*args, **kwargs):
            time.sleep(0.1)
            raise requests.exceptions.ConnectionError("Slow error")

        mock_session.post.side_effect = slow_error

        with pytest.raises(Exception, match="Network error"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_closes_session_successfully(self, client, mock_session):
        await client.close()

        mock_session.close.assert_called_once()

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

    async def test_it_runs_sync_request_in_executor(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_session.post.return_value = mock_response

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_executor = AsyncMock(return_value=({"test": "data"}, 0.1))
            mock_loop.return_value.run_in_executor = mock_executor

            result, response_time = await client.make_rpc_request(
                "192.168.1.100", "Shelly.GetDeviceInfo"
            )

            mock_executor.assert_called_once()
            assert result == {"test": "data"}
            assert response_time == 0.1
