import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from core.domain.entities.exceptions import (
    DeviceAuthenticationError,
    DeviceCommunicationError,
    DeviceUnreachableError,
)
from core.gateways.network.async_shelly_rpc_client import AsyncShellyRPCClient
from core.services.auth_state_cache import AuthStateCache


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
        # auth is passed as keyword argument 'auth', not in headers
        auth_arg = call_args[1].get("auth")
        assert isinstance(auth_arg, httpx.BasicAuth)

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

        with pytest.raises(DeviceCommunicationError, match="HTTP 404: Not Found"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_network_errors(self, client, mock_session):
        mock_session.post.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(DeviceCommunicationError, match="Connection failed"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_timeout_errors(self, client, mock_session):
        mock_session.post.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(DeviceCommunicationError, match="Request timeout"):
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

        with pytest.raises(DeviceCommunicationError, match="Slow error"):
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
        # 401 is handled specially as DeviceAuthenticationError
        status_codes = [400, 403, 500, 503]

        for status_code in status_codes:
            mock_response = MagicMock()
            mock_response.status_code = status_code
            mock_response.text = f"Error {status_code}"
            mock_session.post.return_value = mock_response

            with pytest.raises(DeviceCommunicationError, match=f"HTTP {status_code}"):
                await client.make_rpc_request("192.168.1.100", "Test.Method")

    async def test_it_handles_401_as_auth_error(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_session.post.return_value = mock_response

        # 401 without auth service configured raises DeviceAuthenticationError
        with pytest.raises(
            DeviceAuthenticationError, match="no authentication service is configured"
        ):
            await client.make_rpc_request("192.168.1.100", "Test.Method")

    async def test_it_handles_read_timeout(self, client, mock_session):
        mock_session.post.side_effect = httpx.ReadTimeout("Read timeout")

        with pytest.raises(DeviceCommunicationError, match="Read timeout"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_request_error(self, client, mock_session):
        mock_session.post.side_effect = httpx.RequestError("Request error")

        with pytest.raises(DeviceCommunicationError, match="Request error"):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_handles_pool_timeout(self, client, mock_session):
        mock_session.post.side_effect = httpx.PoolTimeout("Pool timeout")

        # Pool exhaustion is a local condition, not an unreachable host: it must
        # NOT be classified as DeviceUnreachableError (which would skip fallback).
        with pytest.raises(DeviceCommunicationError, match="Pool timeout") as exc_info:
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")
        assert not isinstance(exc_info.value, DeviceUnreachableError)

    async def test_it_flags_connect_errors_as_unreachable(self, client, mock_session):
        mock_session.post.side_effect = httpx.ConnectTimeout("Connect timeout")

        with pytest.raises(DeviceUnreachableError):
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

    async def test_it_names_the_exception_when_it_has_no_text(
        self, client, mock_session
    ):
        mock_session.post.side_effect = httpx.ConnectTimeout("")

        with pytest.raises(DeviceUnreachableError) as exc_info:
            await client.make_rpc_request("192.168.1.100", "Shelly.GetDeviceInfo")

        assert str(exc_info.value).endswith("ConnectTimeout")

    async def test_it_creates_timeout_correctly(self, client, mock_session):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response

        await client.make_rpc_request("192.168.1.100", "Test.Method", timeout=10)

        call_args = mock_session.post.call_args
        timeout_arg = call_args[1]["timeout"]
        # Per-request read timeout is honored; connect is capped for fast dead-IP reject.
        assert isinstance(timeout_arg, httpx.Timeout)
        assert timeout_arg.read == 10
        assert timeout_arg.connect == 2.0

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
        assert isinstance(timeout_arg, httpx.Timeout)
        assert timeout_arg.read == 3.0
        assert timeout_arg.connect == 2.0


class TestAuthStateCacheGating:
    """An empty AuthStateCache is falsy, so presence must decide these paths."""

    async def test_it_clears_auth_state_while_the_cache_is_still_empty(self):
        auth_state_cache = AuthStateCache()
        client = AsyncShellyRPCClient(
            session=AsyncMock(spec=httpx.AsyncClient),
            auth_state_cache=auth_state_cache,
        )

        client._invalidate_auth_cache("192.168.1.100")

        assert auth_state_cache.is_known("192.168.1.100") is True
        assert auth_state_cache.requires_auth("192.168.1.100") is False

    async def test_it_clears_auth_state_for_a_known_mac_while_the_cache_is_empty(self):
        auth_state_cache = AuthStateCache()
        client = AsyncShellyRPCClient(
            session=AsyncMock(spec=httpx.AsyncClient),
            auth_state_cache=auth_state_cache,
        )
        client._ip_to_mac["192.168.1.100"] = "AABBCCDDEEFF"

        client._invalidate_auth_cache("192.168.1.100")

        assert auth_state_cache.is_known("AABBCCDDEEFF") is True


def _ok_response(body: dict | None = None) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = body if body is not None else {"result": {}}
    return response


class TestConnectionBudget:

    @pytest.fixture
    def mock_session(self):
        return AsyncMock(spec=httpx.AsyncClient)

    @staticmethod
    def _track_in_flight(mock_session):
        state = {"now": 0, "peak": 0}

        async def post(*args, **kwargs):
            state["now"] += 1
            state["peak"] = max(state["peak"], state["now"])
            for _ in range(3):
                await asyncio.sleep(0)
            state["now"] -= 1
            return _ok_response()

        mock_session.post.side_effect = post
        return state

    async def test_it_allows_four_connections_per_device_by_default(self, mock_session):
        client = AsyncShellyRPCClient(session=mock_session)
        state = self._track_in_flight(mock_session)

        await asyncio.gather(
            *(client.make_rpc_request("192.168.1.100", "Test.Method") for _ in range(8))
        )

        assert state["peak"] == 4

    @pytest.mark.parametrize("budget", [1, 2, 3])
    async def test_it_caps_concurrent_posts_to_one_device(self, mock_session, budget):
        client = AsyncShellyRPCClient(
            session=mock_session, max_connections_per_device=budget
        )
        state = self._track_in_flight(mock_session)

        await asyncio.gather(
            *(client.make_rpc_request("192.168.1.100", "Test.Method") for _ in range(8))
        )

        assert state["peak"] == budget
        assert mock_session.post.call_count == 8

    async def test_it_gives_each_device_its_own_budget(self, mock_session):
        client = AsyncShellyRPCClient(
            session=mock_session, max_connections_per_device=4
        )
        state = self._track_in_flight(mock_session)

        await asyncio.gather(
            *(
                client.make_rpc_request(ip, "Test.Method")
                for ip in ["192.168.1.100", "192.168.1.101"] * 4
            )
        )

        assert state["peak"] == 8

    async def test_it_answers_an_auth_challenge_at_a_budget_of_one(self, mock_session):
        challenge = MagicMock()
        challenge.status_code = 401
        mock_session.post.side_effect = [
            challenge,
            _ok_response({"result": {"mac": "AABBCCDDEEFF"}}),
            _ok_response({"result": "ok"}),
        ]
        authentication_service = AsyncMock()
        authentication_service.resolve_credentials.return_value = MagicMock(
            username="admin", password="secret"
        )
        client = AsyncShellyRPCClient(
            session=mock_session,
            max_connections_per_device=1,
            authentication_service=authentication_service,
            auth_state_cache=AuthStateCache(),
        )

        result, _ = await asyncio.wait_for(
            client.make_rpc_request("192.168.1.100", "Test.Method"), timeout=1
        )

        assert result == {"result": "ok"}
        assert mock_session.post.call_count == 3

    async def test_it_frees_the_slot_when_a_post_fails(self, mock_session):
        mock_session.post.side_effect = [httpx.ReadTimeout("x"), _ok_response()]
        client = AsyncShellyRPCClient(
            session=mock_session, max_connections_per_device=1
        )

        with pytest.raises(DeviceCommunicationError):
            await client.make_rpc_request("192.168.1.100", "Test.Method")
        await asyncio.wait_for(
            client.make_rpc_request("192.168.1.100", "Test.Method"), timeout=1
        )

        assert client._device_gates == {}

    async def test_it_frees_the_slot_when_a_waiting_request_is_cancelled(
        self, mock_session
    ):
        release = asyncio.Event()

        async def post(*args, **kwargs):
            await release.wait()
            return _ok_response()

        mock_session.post.side_effect = post
        client = AsyncShellyRPCClient(
            session=mock_session, max_connections_per_device=1
        )
        holder = asyncio.create_task(
            client.make_rpc_request("192.168.1.100", "Test.Method")
        )
        waiter = asyncio.create_task(
            client.make_rpc_request("192.168.1.100", "Test.Method")
        )
        await asyncio.sleep(0)

        waiter.cancel()
        release.set()
        await holder

        with pytest.raises(asyncio.CancelledError):
            await waiter
        assert client._device_gates == {}

    @pytest.mark.parametrize("budget", [0, -1])
    def test_it_rejects_a_budget_below_one(self, mock_session, budget):
        with pytest.raises(ValueError, match="max_connections_per_device"):
            AsyncShellyRPCClient(
                session=mock_session, max_connections_per_device=budget
            )

    async def test_it_keeps_a_separate_budget_for_a_port_on_another_host(
        self, mock_session
    ):
        client = AsyncShellyRPCClient(
            session=mock_session, max_connections_per_device=1
        )
        state = self._track_in_flight(mock_session)

        await asyncio.gather(
            client.make_rpc_request("10.0.0.1:80", "Test.Method"),
            client.make_rpc_request("10.0.0.180", "Test.Method"),
        )

        assert state["peak"] == 2

    async def test_it_gives_up_on_a_slot_after_the_request_timeout(self, mock_session):
        release = asyncio.Event()
        sent: list[str] = []

        async def post(*args, **kwargs):
            sent.append(kwargs["json"]["method"])
            await release.wait()
            return _ok_response()

        mock_session.post.side_effect = post
        client = AsyncShellyRPCClient(
            session=mock_session, max_connections_per_device=1
        )
        holder = asyncio.create_task(
            client.make_rpc_request("192.168.1.100", "Slow.Read")
        )
        await asyncio.sleep(0)

        with pytest.raises(DeviceCommunicationError) as exc_info:
            await asyncio.wait_for(
                client.make_rpc_request("192.168.1.100", "Switch.Toggle", timeout=0.05),
                timeout=1,
            )
        release.set()
        await holder

        assert not isinstance(exc_info.value, DeviceUnreachableError)
        assert sent == ["Slow.Read"]
        assert client._device_gates == {}

    async def test_it_sends_a_queued_request_that_gets_a_slot_in_time(
        self, mock_session
    ):
        mock_session.post.return_value = _ok_response()
        client = AsyncShellyRPCClient(
            session=mock_session, max_connections_per_device=1
        )
        state = self._track_in_flight(mock_session)

        await asyncio.gather(
            *(
                client.make_rpc_request("192.168.1.100", "Test.Method", timeout=1)
                for _ in range(4)
            )
        )

        assert state["peak"] == 1
        assert mock_session.post.call_count == 4

    async def test_it_forgets_a_device_after_its_last_request(self, mock_session):
        mock_session.post.return_value = _ok_response()
        client = AsyncShellyRPCClient(session=mock_session)

        await asyncio.gather(
            client.make_rpc_request("192.168.1.100", "Test.Method"),
            client.make_rpc_request("192.168.1.101", "Test.Method"),
        )

        assert client._device_gates == {}
