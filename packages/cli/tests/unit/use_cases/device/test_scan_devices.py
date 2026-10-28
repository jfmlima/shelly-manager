from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.entities import DeviceScanRequest
from cli.use_cases.device.scan_devices import DeviceScanUseCase
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status


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
        return DeviceScanRequest(targets=["192.168.1.1-50"], timeout=3.0, workers=10)

    @pytest.fixture
    def config_scan_request(self):
        return DeviceScanRequest(targets=["192.168.1.100"], timeout=5.0, workers=20)

    @pytest.fixture
    def devices_scan_request(self):
        return DeviceScanRequest(
            targets=["192.168.1.100", "192.168.1.101"], timeout=3.0, workers=10
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

    @pytest.mark.asyncio
    async def test_it_asks_the_scan_for_failed_addresses_when_requested(
        self, scan_use_case, mock_container
    ):
        request = DeviceScanRequest(
            targets=["192.168.1.1"], timeout=3.0, workers=10, include_failed=True
        )
        mock_container.get_scan_interactor.return_value.execute.return_value = []

        await scan_use_case.execute(request)

        scan_request = (
            mock_container.get_scan_interactor.return_value.execute.call_args[0][0]
        )
        assert scan_request.include_failed is True


class TestDeviceScanDisplay:
    @pytest.fixture
    def console(self):
        return MagicMock()

    @pytest.fixture
    def scan_use_case(self, console):
        return DeviceScanUseCase(MagicMock(), console)

    @pytest.fixture
    def results(self):
        return [
            DiscoveredDevice(
                ip="192.168.1.1",
                status=Status.DETECTED,
                device_type="SHSW-1",
                firmware_version="1.0.0",
            ),
            DiscoveredDevice(
                ip="192.168.1.2",
                status=Status.UNREACHABLE,
                error_message="Communication error: ConnectTimeout",
            ),
            DiscoveredDevice(
                ip="192.168.1.3",
                status=Status.ERROR,
                error_message="Device 192.168.1.3 has no device type",
            ),
        ]

    def _printed(self, console):
        return "\n".join(str(call.args[0]) for call in console.print.call_args_list)

    def test_it_prints_a_summary_with_the_counts(self, scan_use_case, console, results):
        scan_use_case.display_results(results, show_table=False)

        output = self._printed(console)
        assert "Scanned 3 addresses: 1 devices, 1 did not answer, 1 failed" in output

    def test_it_always_lists_the_addresses_that_failed(
        self, scan_use_case, console, results
    ):
        scan_use_case.display_results(results, show_table=False)

        output = self._printed(console)
        assert "192.168.1.3" in output
        assert "has no device type" in output

    def test_it_hides_unreachable_addresses_unless_asked(
        self, scan_use_case, console, results
    ):
        scan_use_case.display_results(results, show_table=False)

        output = self._printed(console)
        assert "192.168.1.2" not in output
        assert "--show-unreachable" in output

    def test_it_lists_unreachable_addresses_when_asked(
        self, scan_use_case, console, results
    ):
        scan_use_case.display_results(results, show_table=False, show_unreachable=True)

        output = self._printed(console)
        assert "192.168.1.2" in output
        assert "ConnectTimeout" in output

    def test_it_tables_only_the_devices(self, scan_use_case, results):
        scan_use_case._result_formatter = MagicMock()

        scan_use_case.display_results(results)

        tabled = scan_use_case._result_formatter.format_device_table.call_args[0][0]
        assert [d.ip for d in tabled] == ["192.168.1.1"]

    def test_it_keeps_the_plain_count_when_every_address_answered(
        self, scan_use_case, console, results
    ):
        scan_use_case.display_results(results[:1], show_table=False)

        output = self._printed(console)
        assert "Found 1 devices" in output
        assert "Scanned" not in output
