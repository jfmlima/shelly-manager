from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.entities import FirmwareUpdateRequest
from cli.use_cases.device.firmware_update import FirmwareUpdateUseCase


class TestFirmwareUpdateUseCase:
    @pytest.fixture
    def mock_container(self):
        container = MagicMock()
        container.get_update_interactor.return_value = AsyncMock()
        return container

    @pytest.fixture
    def mock_console(self):
        return MagicMock()

    @pytest.fixture
    def firmware_update_use_case(self, mock_container, mock_console):
        use_case = FirmwareUpdateUseCase(mock_container, mock_console)

        # Mock the progress tracker with proper async context manager
        mock_progress_task = MagicMock()
        mock_progress_task.advance = MagicMock()

        mock_progress_context = AsyncMock()
        mock_progress_context.__aenter__ = AsyncMock(return_value=mock_progress_task)
        mock_progress_context.__aexit__ = AsyncMock(return_value=None)

        use_case._progress_tracker.track_progress = MagicMock(
            return_value=mock_progress_context
        )

        return use_case

    @pytest.fixture
    def basic_request(self):
        return FirmwareUpdateRequest(
            devices=["192.168.1.100"], channel="stable", force=True
        )

    @pytest.fixture
    def scan_request(self):
        return FirmwareUpdateRequest(from_config=True, channel="beta", check_only=True)

    @pytest.fixture
    def mock_action_result(self):
        result = MagicMock()
        result.success = True
        result.data = {
            "update_available": True,
            "current_version": "1.0.0",
            "new_version": "1.1.0",
        }
        return result

    @pytest.fixture
    def mock_no_update_result(self):
        result = MagicMock()
        result.success = True
        result.data = {"update_available": False}
        return result

    @pytest.mark.asyncio
    async def test_execute_with_no_devices_raises_error(self, firmware_update_use_case):
        request = FirmwareUpdateRequest(devices=[], from_config=False)

        with pytest.raises(ValueError, match="No devices specified"):
            await firmware_update_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_execute_basic_update_check_only(
        self,
        firmware_update_use_case,
        basic_request,
        mock_action_result,
        mock_container,
    ):
        basic_request.check_only = True
        mock_container.get_update_interactor.return_value.execute.return_value = (
            mock_action_result
        )

        results = await firmware_update_use_case.execute(basic_request)

        assert len(results) == 1
        assert results[0]["ip"] == "192.168.1.100"
        assert results[0]["update_available"] is True

    @pytest.mark.asyncio
    async def test_execute_no_updates_available(
        self,
        firmware_update_use_case,
        basic_request,
        mock_no_update_result,
        mock_container,
    ):
        mock_container.get_update_interactor.return_value.execute.return_value = (
            mock_no_update_result
        )

        results = await firmware_update_use_case.execute(basic_request)

        assert results == []

    @pytest.mark.asyncio
    async def test_execute_with_force_performs_update(
        self,
        firmware_update_use_case,
        basic_request,
        mock_action_result,
        mock_container,
    ):
        mock_container.get_update_interactor.return_value.execute.return_value = (
            mock_action_result
        )

        results = await firmware_update_use_case.execute(basic_request)

        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["ip"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_execute_with_from_config(
        self, firmware_update_use_case, scan_request, mock_action_result, mock_container
    ):
        mock_device_discovery = AsyncMock()
        mock_devices = [MagicMock(ip="192.168.1.100"), MagicMock(ip="192.168.1.101")]
        mock_device_discovery.discover_devices.return_value = mock_devices
        firmware_update_use_case._device_discovery = mock_device_discovery

        mock_container.get_update_interactor.return_value.execute.return_value = (
            mock_action_result
        )

        results = await firmware_update_use_case.execute(scan_request)

        assert len(results) == 2

    def test_channel_conversion_stable(self, firmware_update_use_case):
        result = firmware_update_use_case._convert_channel_to_enum("stable")
        assert result.value == "stable"

    def test_channel_conversion_beta(self, firmware_update_use_case):
        result = firmware_update_use_case._convert_channel_to_enum("beta")
        assert result.value == "beta"

    @pytest.mark.asyncio
    async def test_execute_handles_update_errors(
        self, firmware_update_use_case, basic_request, mock_container
    ):
        mock_container.get_update_interactor.return_value.execute.side_effect = (
            Exception("Update failed")
        )

        results = await firmware_update_use_case.execute(basic_request)

        assert results == []
