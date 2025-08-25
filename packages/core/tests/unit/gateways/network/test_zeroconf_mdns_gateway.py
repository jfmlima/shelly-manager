import socket
from unittest.mock import AsyncMock, Mock, patch

import pytest
from core.gateways.network.zeroconf_mdns_client import (
    ShellyServiceListener,
    ZeroconfMDNSClient,
)


class TestZeroconfMDNSGateway:
    @pytest.fixture
    def gateway(self):
        return ZeroconfMDNSClient()

    @pytest.fixture
    def mock_aiozc(self):
        mock = Mock()
        mock.zeroconf = Mock()
        return mock

    async def test_discover_device_ips_success(self, gateway):
        """Test successful device discovery."""
        with patch(
            "core.gateways.network.zeroconf_mdns_client.AsyncZeroconf"
        ) as mock_azc_class:
            mock_azc = AsyncMock()
            mock_azc_class.return_value = mock_azc

            with patch(
                "core.gateways.network.zeroconf_mdns_client.ServiceBrowser"
            ) as mock_browser_class:
                mock_browser = Mock()
                mock_browser_class.return_value = mock_browser

                # Simulate discovery by adding IPs to the set
                gateway._discovered_ips.add("192.168.1.100")
                gateway._discovered_ips.add("192.168.1.101")

                result = await gateway.discover_device_ips(timeout=0.1)

                assert len(result) == 2
                assert "192.168.1.100" in result
                assert "192.168.1.101" in result
                mock_browser.cancel.assert_called()

    async def test_discover_device_ips_timeout(self, gateway):
        """Test discovery with timeout."""
        with patch(
            "core.gateways.network.zeroconf_mdns_client.AsyncZeroconf"
        ) as mock_azc_class:
            mock_azc = AsyncMock()
            mock_azc_class.return_value = mock_azc

            with patch(
                "core.gateways.network.zeroconf_mdns_client.ServiceBrowser"
            ) as mock_browser_class:
                mock_browser = Mock()
                mock_browser_class.return_value = mock_browser

                result = await gateway.discover_device_ips(timeout=0.1)

                assert result == []
                mock_browser.cancel.assert_called()

    async def test_discover_device_ips_no_devices(self, gateway):
        """Test discovery when no devices are found."""
        with patch(
            "core.gateways.network.zeroconf_mdns_client.AsyncZeroconf"
        ) as mock_azc_class:
            mock_azc = AsyncMock()
            mock_azc_class.return_value = mock_azc

            with patch(
                "core.gateways.network.zeroconf_mdns_client.ServiceBrowser"
            ) as mock_browser_class:
                mock_browser = Mock()
                mock_browser_class.return_value = mock_browser

                result = await gateway.discover_device_ips(timeout=0.1)

                assert result == []

    async def test_discover_device_ips_exception_handling(self, gateway):
        """Test exception handling during discovery."""
        with patch(
            "core.gateways.network.zeroconf_mdns_client.AsyncZeroconf"
        ) as mock_azc_class:
            mock_azc_class.side_effect = Exception("Zeroconf initialization failed")

            result = await gateway.discover_device_ips(timeout=0.1)

            assert result == []

    async def test_discover_device_ips_custom_service_types(self, gateway):
        """Test discovery with custom service types."""
        custom_types = ["_custom._tcp.local.", "_test._tcp.local."]

        with patch(
            "core.gateways.network.zeroconf_mdns_client.AsyncZeroconf"
        ) as mock_azc_class:
            mock_azc = AsyncMock()
            mock_azc_class.return_value = mock_azc

            with patch(
                "core.gateways.network.zeroconf_mdns_client.ServiceBrowser"
            ) as mock_browser_class:
                mock_browser = Mock()
                mock_browser_class.return_value = mock_browser

                await gateway.discover_device_ips(
                    timeout=0.1, service_types=custom_types
                )

                # Verify ServiceBrowser was called for each service type
                assert mock_browser_class.call_count == 2

    async def test_close_cleanup(self, gateway):
        """Test resource cleanup."""
        mock_azc = AsyncMock()
        gateway._aiozc = mock_azc

        await gateway.close()

        mock_azc.async_close.assert_called_once()
        assert gateway._aiozc is None

    async def test_close_cleanup_exception(self, gateway):
        """Test cleanup handles exceptions gracefully."""
        mock_azc = AsyncMock()
        mock_azc.async_close.side_effect = Exception("Cleanup failed")
        gateway._aiozc = mock_azc

        # Should not raise exception
        await gateway.close()

        mock_azc.async_close.assert_called_once()

    async def test_close_no_aiozc(self, gateway):
        """Test cleanup when no AsyncZeroconf instance exists."""
        # Should not raise exception
        await gateway.close()


class TestShellyServiceListener:
    @pytest.fixture
    def discovered_ips(self):
        return set()

    @pytest.fixture
    def listener(self, discovered_ips):
        return ShellyServiceListener(discovered_ips)

    @pytest.fixture
    def mock_zc(self):
        return Mock()

    def test_add_service_shelly_device(self, listener, mock_zc, discovered_ips):
        """Test adding a Shelly device service."""
        service_name = "shelly1-123456._http._tcp.local."
        service_type = "_http._tcp.local."

        # Mock service info
        mock_info = Mock()
        mock_info.addresses = [socket.inet_aton("192.168.1.100")]
        mock_info.properties = {"device": "shelly"}

        mock_zc.get_service_info.return_value = mock_info

        listener.add_service(mock_zc, service_type, service_name)

        assert "192.168.1.100" in discovered_ips

    def test_add_service_non_shelly_device(self, listener, mock_zc, discovered_ips):
        """Test adding a non-Shelly device service."""
        service_name = "printer._http._tcp.local."
        service_type = "_http._tcp.local."

        # Mock service info
        mock_info = Mock()
        mock_info.addresses = [socket.inet_aton("192.168.1.200")]
        mock_info.properties = {"device": "printer"}

        mock_zc.get_service_info.return_value = mock_info

        listener.add_service(mock_zc, service_type, service_name)

        # Should still add HTTP services for validation by device gateway
        assert "192.168.1.200" in discovered_ips

    def test_add_service_no_info(self, listener, mock_zc, discovered_ips):
        """Test adding service when no service info is available."""
        service_name = "test._http._tcp.local."
        service_type = "_http._tcp.local."

        mock_zc.get_service_info.return_value = None

        listener.add_service(mock_zc, service_type, service_name)

        assert len(discovered_ips) == 0

    def test_add_service_invalid_address(self, listener, mock_zc, discovered_ips):
        """Test handling invalid IP addresses."""
        service_name = "shelly1-123456._http._tcp.local."
        service_type = "_http._tcp.local."

        # Mock service info with invalid address
        mock_info = Mock()
        mock_info.addresses = [b"invalid"]
        mock_info.properties = {"device": "shelly"}

        mock_zc.get_service_info.return_value = mock_info

        with patch("socket.inet_ntoa", side_effect=OSError("Invalid address")):
            listener.add_service(mock_zc, service_type, service_name)

        assert len(discovered_ips) == 0

    def test_add_service_exception_handling(self, listener, mock_zc, discovered_ips):
        """Test exception handling during service addition."""
        service_name = "test._http._tcp.local."
        service_type = "_http._tcp.local."

        mock_zc.get_service_info.side_effect = Exception("Service info failed")

        # Should not raise exception
        listener.add_service(mock_zc, service_type, service_name)

        assert len(discovered_ips) == 0

    def test_is_likely_shelly_device_name_patterns(self, listener):
        """Test Shelly device identification by name patterns."""
        mock_info = Mock()
        mock_info.properties = {}

        # Test various Shelly name patterns
        assert listener._is_likely_shelly_device("shelly1-123456", mock_info) is True
        assert listener._is_likely_shelly_device("shellyplus1-789", mock_info) is True
        assert listener._is_likely_shelly_device("shellypro4pm-abc", mock_info) is True
        assert listener._is_likely_shelly_device("SHELLY1-UPPER", mock_info) is True

        # Test non-Shelly names
        assert listener._is_likely_shelly_device("printer", mock_info) is False
        assert listener._is_likely_shelly_device("router", mock_info) is False

    def test_is_likely_shelly_device_txt_records(self, listener):
        """Test Shelly device identification by TXT records."""
        # Test with Shelly in properties
        mock_info = Mock()
        mock_info.properties = {"manufacturer": "allterco"}

        assert listener._is_likely_shelly_device("device", mock_info) is True

        # Test with non-Shelly properties
        mock_info.properties = {"manufacturer": "other"}
        assert listener._is_likely_shelly_device("device", mock_info) is False

    def test_is_likely_shelly_device_http_service(self, listener):
        """Test HTTP service handling."""
        mock_info = Mock()
        mock_info.properties = {}

        # HTTP services should be accepted for validation by device gateway
        assert (
            listener._is_likely_shelly_device("unknown._http._tcp", mock_info) is True
        )

    def test_remove_service(self, listener, mock_zc):
        """Test service removal (should not raise exception)."""
        listener.remove_service(mock_zc, "_http._tcp.local.", "test")

    def test_update_service(self, listener, mock_zc):
        """Test service update (should not raise exception)."""
        listener.update_service(mock_zc, "_http._tcp.local.", "test")
