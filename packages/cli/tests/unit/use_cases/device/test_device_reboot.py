from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cli.entities import DeviceRebootRequest
from cli.use_cases.device.device_reboot import DeviceRebootUseCase


class TestDeviceRebootUseCase:
    @pytest.fixture
    def mock_container(self):
        container = MagicMock()
        container.get_reboot_interactor.return_value = AsyncMock()
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
    def reboot_use_case(self, mock_container, mock_console, mock_progress_tracker):
        use_case = DeviceRebootUseCase(mock_container, mock_console)
        use_case._progress_tracker.track_progress = MagicMock(
            return_value=mock_progress_tracker
        )
        return use_case

    @pytest.fixture
    def basic_reboot_request(self):
        return DeviceRebootRequest(
            devices=["192.168.1.100", "192.168.1.101"],
            force=True,
            timeout=3.0,
            workers=10,
        )

    @pytest.fixture
    def config_reboot_request(self):
        return DeviceRebootRequest(
            from_config=True, force=False, timeout=5.0, workers=20
        )

    @pytest.fixture
    def sample_reboot_result(self):
        return {
            "ip": "192.168.1.100",
            "success": True,
            "message": "Device rebooted successfully",
            "reboot_initiated": True,
        }

    @pytest.fixture
    def sample_device_list(self):
        device1 = MagicMock()
        device1.ip = "192.168.1.100"
        device2 = MagicMock()
        device2.ip = "192.168.1.101"
        return [device1, device2]

    @pytest.mark.asyncio
    async def test_it_executes_reboot_with_devices(
        self,
        reboot_use_case,
        basic_reboot_request,
        sample_reboot_result,
        mock_container,
    ):
        mock_container.get_reboot_interactor.return_value.execute.return_value = (
            sample_reboot_result
        )

        result = await reboot_use_case.execute(basic_reboot_request)

        assert result is not None
        assert mock_container.get_reboot_interactor.return_value.execute.call_count == 2

    @pytest.mark.asyncio
    @patch("cli.commands.common.confirm_action")
    async def test_it_executes_reboot_from_config(
        self,
        mock_confirm,
        reboot_use_case,
        config_reboot_request,
        sample_device_list,
        sample_reboot_result,
        mock_container,
    ):
        mock_confirm.return_value = True
        mock_container.get_scan_interactor.return_value.execute.return_value = (
            sample_device_list
        )
        mock_container.get_reboot_interactor.return_value.execute.return_value = (
            sample_reboot_result
        )

        result = await reboot_use_case.execute(config_reboot_request)

        assert result is not None
        mock_container.get_scan_interactor.return_value.execute.assert_called_once()
        assert mock_container.get_reboot_interactor.return_value.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_it_validates_no_devices(self, reboot_use_case):
        request = DeviceRebootRequest()

        with pytest.raises(
            ValueError, match="You must specify either device IPs or use --from-config"
        ):
            await reboot_use_case.execute(request)

    @pytest.mark.asyncio
    async def test_it_handles_device_errors(
        self, reboot_use_case, basic_reboot_request, mock_container
    ):
        mock_container.get_reboot_interactor.return_value.execute.side_effect = (
            Exception("Connection failed")
        )

        result = await reboot_use_case.execute(basic_reboot_request)

        assert result is not None
        mock_container.get_reboot_interactor.return_value.execute.assert_called()

    @pytest.mark.asyncio
    @patch("cli.commands.common.confirm_action")
    async def test_it_cancels_reboot_when_user_declines(
        self,
        mock_confirm,
        reboot_use_case,
        config_reboot_request,
        sample_device_list,
        mock_container,
    ):
        mock_confirm.return_value = False
        mock_container.get_scan_interactor.return_value.execute.return_value = (
            sample_device_list
        )
        config_reboot_request.force = False

        with pytest.raises(RuntimeError, match="Reboot cancelled by user"):
            await reboot_use_case.execute(config_reboot_request)
