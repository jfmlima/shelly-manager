from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.entities import DeviceScanRequest
from cli.use_cases.device.scan_devices import DeviceScanUseCase


class TestDeviceScanUseCase:
    @pytest.fixture
    def mock_container(self):
        container = MagicMock()
        container.get_scan_interactor.return_value = AsyncMock()
        return container

    @pytest.fixture
    def mock_console(self):
        return MagicMock()

    @pytest.fixture
    def scan_use_case(self, mock_container, mock_console):
        return DeviceScanUseCase(mock_container, mock_console)

    @pytest.fixture
    def basic_scan_request(self):
        return DeviceScanRequest(
            ip_ranges=["192.168.1.1-192.168.1.50"], timeout=3.0, workers=10
        )

    @pytest.fixture
    def config_scan_request(self):
        return DeviceScanRequest(from_config=True, timeout=5.0, workers=20)

    @pytest.fixture
    def devices_scan_request(self):
        return DeviceScanRequest(
            devices=["192.168.1.100", "192.168.1.101"], timeout=3.0, workers=10
        )

    @pytest.fixture
    def sample_device_list(self):
        device1 = MagicMock()
        device1.ip = "192.168.1.100"
        device1.device_type = "SHSW-25"
        device1.firmware_version = "1.0.0"

        device2 = MagicMock()
        device2.ip = "192.168.1.101"
        device2.device_type = "SHSW-1"
        device2.firmware_version = "1.1.0"

        return [device1, device2]

    @pytest.mark.asyncio
    async def test_it_executes_scan_with_ip_ranges(
        self, scan_use_case, basic_scan_request, sample_device_list, mock_container
    ):
        mock_container.get_scan_interactor.return_value.execute.return_value = (
            sample_device_list
        )

        result = await scan_use_case.execute(basic_scan_request)

        assert result == sample_device_list
        mock_container.get_scan_interactor.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_it_executes_scan_from_config(
        self, scan_use_case, config_scan_request, sample_device_list, mock_container
    ):
        mock_container.get_scan_interactor.return_value.execute.return_value = (
            sample_device_list
        )

        result = await scan_use_case.execute(config_scan_request)

        assert result == sample_device_list
        mock_container.get_scan_interactor.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_it_executes_scan_with_specific_devices(
        self, scan_use_case, devices_scan_request, sample_device_list, mock_container
    ):
        mock_container.get_scan_interactor.return_value.execute.return_value = (
            sample_device_list
        )

        result = await scan_use_case.execute(devices_scan_request)

        assert result == sample_device_list
        mock_container.get_scan_interactor.return_value.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_it_executes_scan_no_devices_found(
        self, scan_use_case, basic_scan_request, mock_container
    ):
        mock_container.get_scan_interactor.return_value.execute.return_value = []

        result = await scan_use_case.execute(basic_scan_request)

        assert result == []
        mock_container.get_scan_interactor.return_value.execute.assert_called_once()
