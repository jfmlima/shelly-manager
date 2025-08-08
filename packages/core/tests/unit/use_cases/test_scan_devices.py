from unittest.mock import AsyncMock

import pytest
from core.domain.entities.exceptions import ValidationError
from core.domain.entities.shelly_device import ShellyDevice
from core.domain.enums.enums import DeviceStatus
from core.domain.value_objects.scan_request import ScanRequest
from core.use_cases.scan_devices import ScanDevicesUseCase


class TestScanDevicesUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway, mock_config_gateway):
        return ScanDevicesUseCase(
            device_gateway=mock_device_gateway, config_gateway=mock_config_gateway
        )

    @pytest.fixture
    def valid_scan_request(self):
        return ScanRequest(
            start_ip="192.168.1.1",
            end_ip="192.168.1.5",
            use_predefined=False,
            timeout=3.0,
            max_workers=10,
        )

    @pytest.fixture
    def predefined_scan_request(self):
        return ScanRequest(use_predefined=True, timeout=3.0, max_workers=10)

    async def test_it_scans_ip_range_successfully(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        mock_device = ShellyDevice(
            ip="192.168.1.1",
            status=DeviceStatus.DETECTED,
            device_id="test-device-1",
            device_type="Shelly1",
            firmware_version="1.14.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=mock_device)

        result = await use_case.execute(valid_scan_request)

        assert len(result) == 5
        assert all(device.status == DeviceStatus.DETECTED for device in result)
        assert mock_device_gateway.discover_device.call_count == 5

    async def test_it_scans_predefined_ips_successfully(
        self,
        use_case,
        predefined_scan_request,
        mock_device_gateway,
        mock_config_gateway,
    ):
        predefined_ips = ["192.168.1.100", "192.168.1.101"]
        mock_config_gateway.get_predefined_ips = AsyncMock(return_value=predefined_ips)

        mock_device = ShellyDevice(
            ip="192.168.1.100",
            status=DeviceStatus.DETECTED,
            device_id="test-device-1",
            device_type="Shelly1",
            firmware_version="1.14.0",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=mock_device)

        result = await use_case.execute(predefined_scan_request)

        assert len(result) == 2
        assert all(device.status == DeviceStatus.DETECTED for device in result)
        mock_config_gateway.get_predefined_ips.assert_called_once()
        assert mock_device_gateway.discover_device.call_count == 2

    async def test_it_returns_empty_list_when_no_devices_found(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        result = await use_case.execute(valid_scan_request)

        assert len(result) == 0
        assert mock_device_gateway.discover_device.call_count == 5

    async def test_it_returns_empty_list_when_no_predefined_ips(
        self, use_case, predefined_scan_request, mock_config_gateway
    ):
        mock_config_gateway.get_predefined_ips = AsyncMock(return_value=[])

        result = await use_case.execute(predefined_scan_request)

        assert len(result) == 0
        mock_config_gateway.get_predefined_ips.assert_called_once()

    async def test_it_filters_out_non_detected_devices(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        devices = [
            ShellyDevice(
                ip="192.168.1.1",
                status=DeviceStatus.DETECTED,
                device_id="1",
                device_type="Shelly1",
                firmware_version="1.14.0",
            ),
            ShellyDevice(
                ip="192.168.1.2",
                status=DeviceStatus.ERROR,
                device_id="2",
                device_type="Shelly1",
                firmware_version="1.14.0",
            ),
            ShellyDevice(
                ip="192.168.1.3",
                status=DeviceStatus.DETECTED,
                device_id="3",
                device_type="Shelly1",
                firmware_version="1.14.0",
            ),
        ]
        mock_device_gateway.discover_device = AsyncMock()
        mock_device_gateway.discover_device.side_effect = devices + [None, None]

        result = await use_case.execute(valid_scan_request)

        assert len(result) == 2
        assert all(device.status == DeviceStatus.DETECTED for device in result)

    async def test_it_validates_scan_request_with_missing_ips(self, use_case):
        invalid_request = ScanRequest(
            start_ip=None,
            end_ip=None,
            use_predefined=False,
            timeout=3.0,
            max_workers=10,
        )

        with pytest.raises(ValidationError):
            await use_case.execute(invalid_request)

    async def test_it_handles_discovery_service_exceptions(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        mock_device_gateway.discover_device = AsyncMock(
            side_effect=Exception("Connection error")
        )

        result = await use_case.execute(valid_scan_request)

        assert len(result) == 0

    async def test_it_generates_correct_ip_range(self, use_case):
        request = ScanRequest(
            start_ip="192.168.1.1",
            end_ip="192.168.1.3",
            use_predefined=False,
            timeout=3.0,
            max_workers=10,
        )

        ips = use_case._generate_ip_range(request.start_ip, request.end_ip)

        expected_ips = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
        assert ips == expected_ips

    async def test_it_respects_max_workers_parameter(
        self, use_case, mock_device_gateway
    ):
        request = ScanRequest(
            start_ip="192.168.1.1",
            end_ip="192.168.1.100",
            use_predefined=False,
            timeout=3.0,
            max_workers=5,
        )

        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        await use_case.execute(request)

        assert mock_device_gateway.discover_device.call_count == 100

    async def test_it_respects_timeout_parameter(
        self, use_case, valid_scan_request, mock_device_gateway
    ):
        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        await use_case.execute(valid_scan_request)

        for call in mock_device_gateway.discover_device.call_args_list:
            assert call[0][1] == valid_scan_request.timeout
