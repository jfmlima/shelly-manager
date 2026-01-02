from unittest.mock import AsyncMock

import pytest
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status
from core.domain.value_objects.scan_request import ScanRequest
from core.gateways.network import MDNSGateway
from core.use_cases.scan_devices import ScanDevicesUseCase


class TestScanDevicesUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return ScanDevicesUseCase(device_gateway=mock_device_gateway)

    @pytest.fixture
    def valid_scan_request(self):
        return ScanRequest(
            targets=["192.168.1.1-5"],
            use_predefined=False,
            use_mdns=False,
            timeout=3.0,
            max_workers=10,
        )

    @pytest.fixture
    def predefined_scan_request(self):
        return ScanRequest(
            use_predefined=True, use_mdns=False, timeout=3.0, max_workers=10
        )

    async def test_it_scans_ip_range_successfully(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        mock_device = DiscoveredDevice(
            ip="192.168.1.1",
            status=Status.DETECTED,
            device_id="test-device-1",
            device_type="Shelly1",
            firmware_version="1.14.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=mock_device)

        result = await use_case.execute(valid_scan_request)

        assert len(result) == 5
        assert all(device.status == Status.DETECTED for device in result)
        assert mock_device_gateway.discover_device.call_count == 5

    async def test_it_returns_empty_list_when_no_devices_found(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        result = await use_case.execute(valid_scan_request)

        assert len(result) == 0
        assert mock_device_gateway.discover_device.call_count == 5

    async def test_it_filters_out_non_detected_devices(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        devices = [
            DiscoveredDevice(
                ip="192.168.1.1",
                status=Status.DETECTED,
                device_id="1",
                device_type="Shelly1",
                firmware_version="1.14.0",
            ),
            DiscoveredDevice(
                ip="192.168.1.2",
                status=Status.ERROR,
                device_id="2",
                device_type="Shelly1",
                firmware_version="1.14.0",
            ),
            DiscoveredDevice(
                ip="192.168.1.3",
                status=Status.DETECTED,
                device_id="3",
                device_type="Shelly1",
                firmware_version="1.14.0",
            ),
        ]
        mock_device_gateway.discover_device = AsyncMock()
        mock_device_gateway.discover_device.side_effect = devices + [None, None]

        result = await use_case.execute(valid_scan_request)

        assert len(result) == 2
        assert all(device.status == Status.DETECTED for device in result)

    async def test_it_handles_discovery_service_exceptions(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        mock_device_gateway.discover_device = AsyncMock(
            side_effect=Exception("Connection error")
        )

        result = await use_case.execute(valid_scan_request)

        assert len(result) == 0

    async def test_it_respects_max_workers_parameter(
        self, use_case, mock_device_gateway
    ):
        request = ScanRequest(
            targets=["192.168.1.1-100"],
            use_predefined=False,
            use_mdns=False,
            timeout=3.0,
            max_workers=5,
        )

        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        await use_case.execute(request)

        assert mock_device_gateway.discover_device.call_count == 100

    @pytest.fixture
    def mock_mdns_client(self):
        return AsyncMock(spec=MDNSGateway)

    @pytest.fixture
    def use_case_with_mdns(self, mock_device_gateway, mock_mdns_client):
        return ScanDevicesUseCase(
            device_gateway=mock_device_gateway,
            mdns_client=mock_mdns_client,
        )

    @pytest.fixture
    def mdns_scan_request(self):
        return ScanRequest(
            use_mdns=True, use_predefined=False, timeout=5.0, max_workers=10
        )

    async def test_it_scans_with_mdns_discovery_success(
        self,
        use_case_with_mdns,
        mdns_scan_request,
        mock_mdns_client,
        mock_device_gateway,
    ):
        mock_mdns_client.discover_device_ips.return_value = [
            "192.168.1.100",
            "192.168.1.101",
        ]

        mock_device = DiscoveredDevice(
            ip="192.168.1.100",
            status=Status.DETECTED,
            device_id="shelly1-123456",
            device_type="Shelly1",
            firmware_version="1.14.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=mock_device)

        result = await use_case_with_mdns.execute(mdns_scan_request)

        assert len(result) == 2
        assert all(device.status == Status.DETECTED for device in result)
        mock_mdns_client.discover_device_ips.assert_called_once_with(timeout=5.0)
        assert mock_device_gateway.discover_device.call_count == 2

    async def test_it_scans_with_mdns_no_devices_found(
        self, use_case_with_mdns, mdns_scan_request, mock_mdns_client
    ):
        mock_mdns_client.discover_device_ips.return_value = []

        result = await use_case_with_mdns.execute(mdns_scan_request)

        assert result == []
        mock_mdns_client.discover_device_ips.assert_called_once_with(timeout=5.0)

    async def test_it_scans_with_mdns_client_unavailable(
        self, mock_device_gateway, mdns_scan_request
    ):
        use_case = ScanDevicesUseCase(
            device_gateway=mock_device_gateway,
            mdns_client=None,
        )

        result = await use_case.execute(mdns_scan_request)

        assert result == []

    async def test_it_scans_with_mdns_client_exception(
        self, use_case_with_mdns, mdns_scan_request, mock_mdns_client
    ):
        mock_mdns_client.discover_device_ips.side_effect = Exception("mDNS failed")

        result = await use_case_with_mdns.execute(mdns_scan_request)

        assert result == []
        mock_mdns_client.discover_device_ips.assert_called_once_with(timeout=5.0)
