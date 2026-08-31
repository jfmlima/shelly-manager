from unittest.mock import AsyncMock

import pytest
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.entities.exceptions import ConfigurationError
from core.domain.enums.enums import Status
from core.domain.value_objects.firmware_release import FirmwareRelease
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

    async def test_it_surfaces_a_configuration_error_rather_than_scanning_empty(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        mock_device_gateway.discover_device = AsyncMock(
            side_effect=ConfigurationError(
                "encryption", "SHELLY_SECRET_KEY is not set."
            )
        )

        with pytest.raises(ConfigurationError) as excinfo:
            await use_case.execute(valid_scan_request)

        assert "SHELLY_SECRET_KEY" in str(excinfo.value)

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

    async def test_it_forwards_request_timeout_to_gateway(
        self, use_case, mock_device_gateway
    ):
        request = ScanRequest(
            targets=["192.168.1.5"],
            use_mdns=False,
            timeout=1.5,
            max_workers=10,
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        await use_case.execute(request)

        mock_device_gateway.discover_device.assert_awaited_once_with(
            "192.168.1.5", timeout=1.5
        )

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


class TestScanSettlesUpdateStatus:
    """A stalled device-side update check is answered from the manager's index."""

    @pytest.fixture
    def single_ip_request(self):
        return ScanRequest(
            targets=["192.168.1.1"],
            use_predefined=False,
            use_mdns=False,
            timeout=3.0,
            max_workers=10,
        )

    def _device(self, status=Status.DETECTED, **kwargs):
        base = {
            "ip": "192.168.1.1",
            "status": status,
            "device_id": "1",
            "device_type": "SNSW-102P16EU",
            "app_name": "Plus2PM",
            "firmware_version": "20240101-000000/1.7.5-gabc",
        }
        base.update(kwargs)
        return DiscoveredDevice(**base)

    def _use_case(self, mock_device_gateway, release):
        firmware_gateway = AsyncMock()
        if isinstance(release, Exception):
            firmware_gateway.get_latest = AsyncMock(side_effect=release)
        else:
            firmware_gateway.get_latest = AsyncMock(return_value=release)
        use_case = ScanDevicesUseCase(
            device_gateway=mock_device_gateway,
            firmware_gateway=firmware_gateway,
        )
        return use_case, firmware_gateway

    async def test_it_marks_an_update_the_index_publishes(
        self, mock_device_gateway, single_ip_request
    ):
        mock_device_gateway.discover_device = AsyncMock(return_value=self._device())
        use_case, firmware_gateway = self._use_case(
            mock_device_gateway,
            FirmwareRelease(
                app_name="Plus2PM",
                version="1.8.0",
                build_id="20250611-100000/1.8.0-g1234567",
                download_url="https://fwcdn.example.test/Plus2PM.zip",
            ),
        )

        result = await use_case.execute(single_ip_request)

        assert result[0].status == Status.UPDATE_AVAILABLE
        assert result[0].available_firmware_version == "1.8.0"
        assert result[0].available_firmware_channel == "stable"
        firmware_gateway.get_latest.assert_awaited_once_with("Plus2PM")

    async def test_it_marks_a_device_already_on_the_published_build(
        self, mock_device_gateway, single_ip_request
    ):
        build_id = "20250611-100000/1.7.5-g1234567"
        mock_device_gateway.discover_device = AsyncMock(
            return_value=self._device(firmware_version=build_id)
        )
        use_case, _ = self._use_case(
            mock_device_gateway,
            FirmwareRelease(
                app_name="Plus2PM",
                version="1.7.5",
                build_id=build_id,
                download_url="https://fwcdn.example.test/Plus2PM.zip",
            ),
        )

        result = await use_case.execute(single_ip_request)

        assert result[0].status == Status.NO_UPDATE_NEEDED
        assert result[0].available_firmware_version is None

    async def test_it_leaves_detected_when_the_index_has_no_release(
        self, mock_device_gateway, single_ip_request
    ):
        mock_device_gateway.discover_device = AsyncMock(return_value=self._device())
        use_case, _ = self._use_case(mock_device_gateway, None)

        result = await use_case.execute(single_ip_request)

        assert result[0].status == Status.DETECTED

    async def test_it_leaves_detected_when_the_index_is_unreachable(
        self, mock_device_gateway, single_ip_request
    ):
        mock_device_gateway.discover_device = AsyncMock(return_value=self._device())
        use_case, _ = self._use_case(mock_device_gateway, Exception("index down"))

        result = await use_case.execute(single_ip_request)

        assert result[0].status == Status.DETECTED

    async def test_it_leaves_a_settled_status_alone(
        self, mock_device_gateway, single_ip_request
    ):
        mock_device_gateway.discover_device = AsyncMock(
            return_value=self._device(status=Status.NO_UPDATE_NEEDED)
        )
        use_case, firmware_gateway = self._use_case(mock_device_gateway, None)

        result = await use_case.execute(single_ip_request)

        assert result[0].status == Status.NO_UPDATE_NEEDED
        firmware_gateway.get_latest.assert_not_awaited()

    async def test_it_keeps_the_device_reported_available_version(
        self, mock_device_gateway, single_ip_request
    ):
        mock_device_gateway.discover_device = AsyncMock(
            return_value=self._device(
                status=Status.UPDATE_AVAILABLE,
                available_firmware_version="1.9.0",
            )
        )
        use_case, firmware_gateway = self._use_case(mock_device_gateway, None)

        result = await use_case.execute(single_ip_request)

        assert result[0].status == Status.UPDATE_AVAILABLE
        assert result[0].available_firmware_version == "1.9.0"
        assert result[0].available_firmware_channel is None
        firmware_gateway.get_latest.assert_not_awaited()

    async def test_it_skips_a_device_without_an_app_name(
        self, mock_device_gateway, single_ip_request
    ):
        mock_device_gateway.discover_device = AsyncMock(
            return_value=self._device(app_name=None)
        )
        use_case, firmware_gateway = self._use_case(mock_device_gateway, None)

        result = await use_case.execute(single_ip_request)

        assert result[0].status == Status.DETECTED
        firmware_gateway.get_latest.assert_not_awaited()

    async def test_it_asks_the_index_once_per_app(self, mock_device_gateway):
        request = ScanRequest(
            targets=["192.168.1.1", "192.168.1.2"],
            use_predefined=False,
            use_mdns=False,
            timeout=3.0,
            max_workers=10,
        )
        mock_device_gateway.discover_device = AsyncMock(
            side_effect=lambda ip, timeout: self._device(ip=ip)
        )
        use_case, firmware_gateway = self._use_case(mock_device_gateway, None)

        await use_case.execute(request)

        firmware_gateway.get_latest.assert_awaited_once_with("Plus2PM")
