import asyncio
import socket
from unittest.mock import AsyncMock, Mock

import pytest
from core.gateways.network.zeroconf_mdns_client import (
    ShellyServiceListener,
    ZeroconfMDNSClient,
)


class TestZeroconfMDNSGateway:
    @pytest.fixture
    def aiozc(self):
        instance = Mock()
        instance.zeroconf = Mock()
        instance.async_close = AsyncMock()
        return instance

    @pytest.fixture
    def browser(self):
        instance = Mock()
        instance.async_cancel = AsyncMock()
        return instance

    @pytest.fixture
    def browser_factory(self, browser):
        return Mock(return_value=browser)

    @pytest.fixture
    def gateway(self, aiozc, browser_factory):
        return ZeroconfMDNSClient(
            aiozc_factory=Mock(return_value=aiozc),
            browser_factory=browser_factory,
        )

    async def test_it_discovers_device_ips_successfully(
        self, gateway, browser, browser_factory
    ):
        """Devices added by the listener during the scan are returned."""

        def add_ip(_zeroconf, _service_type, listener=None):
            listener.discovered_ips.add("192.168.1.100")
            return browser

        browser_factory.side_effect = add_ip

        result = await gateway.discover_device_ips(timeout=0)

        assert result == ["192.168.1.100"]

    async def test_it_returns_empty_list_when_no_devices_found(self, gateway):
        result = await gateway.discover_device_ips(timeout=0)

        assert result == []

    async def test_it_creates_a_browser_for_each_service_type(
        self, gateway, browser_factory
    ):
        custom_types = ["_custom._tcp.local.", "_test._tcp.local."]

        await gateway.discover_device_ips(timeout=0, service_types=custom_types)

        assert browser_factory.call_count == len(custom_types)

    async def test_it_cancels_browsers_and_closes_zeroconf(
        self, gateway, browser, aiozc
    ):
        await gateway.discover_device_ips(timeout=0)

        browser.async_cancel.assert_awaited()
        aiozc.async_close.assert_awaited_once()

    async def test_it_returns_empty_list_on_initialization_error(self, browser_factory):
        """If the AsyncZeroconf factory raises, discovery is caught and returns []."""
        gateway = ZeroconfMDNSClient(
            aiozc_factory=Mock(side_effect=Exception("init failed")),
            browser_factory=browser_factory,
        )

        result = await gateway.discover_device_ips(timeout=0)

        assert result == []

    async def test_it_awaits_pending_resolutions_before_returning(
        self, gateway, browser, browser_factory
    ):
        """Services resolved off-thread via the listener are gathered before return."""

        def resolve_a_shelly(_zeroconf, _service_type, listener=None):
            info = Mock()
            info.addresses = [socket.inet_aton("192.168.1.50")]
            info.properties = {}
            zc = Mock()
            zc.get_service_info.return_value = info
            listener.add_service(
                zc, "_http._tcp.local.", "shelly1-abc._http._tcp.local."
            )
            return browser

        browser_factory.side_effect = resolve_a_shelly

        result = await gateway.discover_device_ips(timeout=0)

        assert result == ["192.168.1.50"]

    async def test_it_close_is_a_noop(self, gateway):
        """close() no longer manages state; each scan cleans up after itself."""
        await gateway.close()

        assert not hasattr(gateway, "_aiozc")


class TestShellyServiceListener:
    @pytest.fixture
    def discovered_ips(self):
        return set()

    @pytest.fixture
    def listener(self, discovered_ips):
        return ShellyServiceListener(discovered_ips, Mock())

    @pytest.fixture
    def mock_zc(self):
        return Mock()

    def test_it_adds_shelly_device_ip(self, listener, mock_zc, discovered_ips):
        info = Mock()
        info.addresses = [socket.inet_aton("192.168.1.100")]
        info.properties = {"device": "shelly"}
        mock_zc.get_service_info.return_value = info

        listener._resolve_service(
            mock_zc, "_http._tcp.local.", "shelly1-123456._http._tcp.local."
        )

        assert "192.168.1.100" in discovered_ips

    def test_it_adds_http_service_ip(self, listener, mock_zc, discovered_ips):
        """Non-Shelly HTTP services are kept for validation by the device gateway."""
        info = Mock()
        info.addresses = [socket.inet_aton("192.168.1.200")]
        info.properties = {"device": "printer"}
        mock_zc.get_service_info.return_value = info

        listener._resolve_service(
            mock_zc, "_http._tcp.local.", "printer._http._tcp.local."
        )

        assert "192.168.1.200" in discovered_ips

    def test_it_skips_non_shelly_non_http_service(
        self, listener, mock_zc, discovered_ips
    ):
        info = Mock()
        info.addresses = [socket.inet_aton("192.168.1.201")]
        info.properties = {"device": "printer"}
        mock_zc.get_service_info.return_value = info

        listener._resolve_service(
            mock_zc, "_ipp._tcp.local.", "printer._ipp._tcp.local."
        )

        assert len(discovered_ips) == 0

    def test_it_skips_when_no_service_info(self, listener, mock_zc, discovered_ips):
        mock_zc.get_service_info.return_value = None

        listener._resolve_service(
            mock_zc, "_http._tcp.local.", "test._http._tcp.local."
        )

        assert len(discovered_ips) == 0

    def test_it_handles_invalid_address(self, listener, mock_zc, discovered_ips):
        info = Mock()
        info.addresses = [b"invalid"]  # not 4 bytes -> socket.inet_ntoa raises OSError
        info.properties = {"device": "shelly"}
        mock_zc.get_service_info.return_value = info

        listener._resolve_service(
            mock_zc, "_http._tcp.local.", "shelly1-123456._http._tcp.local."
        )

        assert len(discovered_ips) == 0

    def test_it_handles_resolution_exception(self, listener, mock_zc, discovered_ips):
        mock_zc.get_service_info.side_effect = Exception("Service info failed")

        # Should not raise
        listener._resolve_service(
            mock_zc, "_http._tcp.local.", "test._http._tcp.local."
        )

        assert len(discovered_ips) == 0

    async def test_it_schedules_resolution_off_the_event_loop(self):
        """add_service offloads the blocking resolve and tracks the future."""
        discovered: set[str] = set()
        listener = ShellyServiceListener(discovered, asyncio.get_running_loop())

        info = Mock()
        info.addresses = [socket.inet_aton("192.168.1.77")]
        info.properties = {}
        mock_zc = Mock()
        mock_zc.get_service_info.return_value = info

        listener.add_service(
            mock_zc, "_http._tcp.local.", "shelly1-x._http._tcp.local."
        )

        assert len(listener.pending_futures) == 1
        await asyncio.gather(*listener.pending_futures)
        assert "192.168.1.77" in discovered

    def test_it_identifies_shelly_devices_by_name(self, listener):
        info = Mock()
        info.properties = {}

        assert listener._is_likely_shelly_device("shelly1-123456", info) is True
        assert listener._is_likely_shelly_device("shellyplus1-789", info) is True
        assert listener._is_likely_shelly_device("shellypro4pm-abc", info) is True
        assert listener._is_likely_shelly_device("SHELLY1-UPPER", info) is True

        assert listener._is_likely_shelly_device("router", info) is False

    def test_it_identifies_shelly_devices_by_txt_records(self, listener):
        info = Mock()
        info.properties = {"manufacturer": "allterco"}
        assert listener._is_likely_shelly_device("device", info) is True

        info.properties = {"manufacturer": "other"}
        assert listener._is_likely_shelly_device("device", info) is False

    def test_it_identifies_http_services(self, listener):
        info = Mock()
        info.properties = {}

        assert listener._is_likely_shelly_device("unknown._http._tcp", info) is True

    def test_it_ignores_removed_services(self, listener, mock_zc):
        # Should not raise
        listener.remove_service(mock_zc, "_http._tcp.local.", "test")

    def test_it_ignores_updated_services(self, listener, mock_zc):
        # Should not raise
        listener.update_service(mock_zc, "_http._tcp.local.", "test")
