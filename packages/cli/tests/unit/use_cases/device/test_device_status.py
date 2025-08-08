from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.entities import DeviceStatusRequest
from cli.use_cases.device.device_status import DeviceStatusUseCase


class TestDeviceStatusUseCase:
    @pytest.fixture
    def mock_container(self):
        container = MagicMock()
        container.get_status_interactor.return_value = AsyncMock()
        container.get_scan_interactor.return_value = AsyncMock()
        return container

    @pytest.fixture
    def mock_console(self):
        return MagicMock()

    @pytest.fixture
    def mock_progress_tracker(self):
        mock_progress_task = MagicMock()
        mock_progress_task.advance = MagicMock()

        mock_progress_context = AsyncMock()
        mock_progress_context.__aenter__ = AsyncMock(return_value=mock_progress_task)
        mock_progress_context.__aexit__ = AsyncMock(return_value=None)

        return mock_progress_context

    @pytest.fixture
    def status_use_case(self, mock_container, mock_console, mock_progress_tracker):
        use_case = DeviceStatusUseCase(mock_container, mock_console)
        use_case._progress_tracker.track_progress = MagicMock(
            return_value=mock_progress_tracker
        )
        return use_case

    @pytest.fixture
    def basic_status_request(self):
        return DeviceStatusRequest(
            devices=["192.168.1.100", "192.168.1.101"],
            include_updates=True,
            timeout=3.0,
            workers=10,
        )

    @pytest.fixture
    def config_status_request(self):
        return DeviceStatusRequest(
            from_config=True,
            include_updates=False,
            timeout=5.0,
            workers=20,
            verbose=True,
        )

    @pytest.fixture
    def sample_status_result(self):
        return {
            "ip": "192.168.1.100",
            "success": True,
            "device_type": "SHSW-25",
            "firmware_version": "1.0.0",
            "device_name": "Living Room Switch",
            "update_available": True,
            "new_firmware_version": "1.1.0",
        }

    @pytest.fixture
    def sample_device_list(self):
        device1 = MagicMock()
        device1.ip = "192.168.1.100"
        device2 = MagicMock()
        device2.ip = "192.168.1.101"
        return [device1, device2]

    @pytest.mark.asyncio
    async def test_it_executes_status_with_devices(
        self,
        status_use_case,
        basic_status_request,
        sample_status_result,
        mock_container,
    ):
        mock_container.get_status_interactor.return_value.execute.return_value = (
            sample_status_result
        )

        result = await status_use_case.execute(basic_status_request)

        assert result is not None
        assert mock_container.get_status_interactor.return_value.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_it_executes_status_from_config(
        self,
        status_use_case,
        config_status_request,
        sample_device_list,
        sample_status_result,
        mock_container,
    ):
        mock_container.get_scan_interactor.return_value.execute.return_value = (
            sample_device_list
        )
        mock_container.get_status_interactor.return_value.execute.return_value = (
            sample_status_result
        )

        result = await status_use_case.execute(config_status_request)

        assert result is not None
        mock_container.get_scan_interactor.return_value.execute.assert_called_once()
        assert mock_container.get_status_interactor.return_value.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_it_validates_no_devices(self, status_use_case):
        request = DeviceStatusRequest()

        with pytest.raises(
            ValueError, match="You must specify either device IPs or use --from-config"
        ):
            await status_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_it_handles_device_errors(
        self, status_use_case, basic_status_request, mock_container
    ):
        mock_container.get_status_interactor.return_value.execute.side_effect = (
            Exception("Connection timeout")
        )

        result = await status_use_case.execute(basic_status_request)

        assert result is not None
        mock_container.get_status_interactor.return_value.execute.assert_called()
