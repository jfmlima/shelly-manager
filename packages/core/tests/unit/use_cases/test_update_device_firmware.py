from unittest.mock import AsyncMock

import pytest
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.entities.exceptions import DeviceValidationError
from core.domain.enums.enums import Status, UpdateChannel
from core.domain.value_objects.action_result import ActionResult
from core.domain.value_objects.bulk_update_device_firmware_request import (
    BulkUpdateDeviceFirmwareRequest,
)
from core.domain.value_objects.update_device_firmware_request import (
    UpdateDeviceFirmwareRequest,
)
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase


class TestUpdateDeviceFirmwareUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return UpdateDeviceFirmwareUseCase(device_gateway=mock_device_gateway)

    async def test_it_updates_firmware_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Firmware update started successfully",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        request = UpdateDeviceFirmwareRequest(device_ip=device_ip)
        result = await use_case.execute(request)

        assert result.success is True
        assert result.action_type == "update"
        assert result.device_ip == device_ip
        assert result.message == "Firmware update started successfully"
        mock_device_gateway.discover_device.assert_called_once_with(device_ip)
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "stable"}
        )

    async def test_it_updates_firmware_with_beta_channel(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Beta firmware update started",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(
            UpdateDeviceFirmwareRequest(device_ip=device_ip, channel=UpdateChannel.BETA)
        )

        assert result.success is True
        assert result.message == "Beta firmware update started"
        mock_device_gateway.discover_device.assert_called_once_with(device_ip)
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "beta"}
        )

    async def test_it_handles_update_failure(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        expected_result = ActionResult(
            success=False,
            action_type="update",
            device_ip=device_ip,
            message="Firmware update failed",
            error="Device already has latest firmware",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(
            UpdateDeviceFirmwareRequest(device_ip=device_ip)
        )

        assert result.success is False
        assert result.action_type == "update"
        assert result.error == "Device already has latest firmware"
        mock_device_gateway.discover_device.assert_called_once_with(device_ip)
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "stable"}
        )

    async def test_it_passes_additional_parameters(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        additional_params = {"timeout": 300}
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Forced firmware update started",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(
            UpdateDeviceFirmwareRequest(
                device_ip=device_ip, channel=UpdateChannel.STABLE
            ),
            **additional_params,
        )

        assert result.success is True
        assert result.message == "Forced firmware update started"
        expected_params = {"channel": "stable", "timeout": 300}
        mock_device_gateway.discover_device.assert_called_once_with(device_ip)
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", expected_params
        )

    async def test_it_defaults_to_stable_channel(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Firmware update started",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(
            UpdateDeviceFirmwareRequest(device_ip=device_ip)
        )

        assert result.success is True
        mock_device_gateway.discover_device.assert_called_once_with(device_ip)
        mock_device_gateway.execute_action.assert_called_once_with(
            device_ip, "update", {"channel": "stable"}
        )

    async def test_it_handles_auth_required_device(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        expected_result = ActionResult(
            success=False,
            action_type="update",
            device_ip=device_ip,
            message="Authentication required",
            error="Device requires username and password",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(
            UpdateDeviceFirmwareRequest(device_ip=device_ip)
        )

        assert result.success is False
        assert result.error == "Device requires username and password"

    async def test_it_handles_offline_device(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        expected_result = ActionResult(
            success=False,
            action_type="update",
            device_ip=device_ip,
            message="Device is offline",
            error="Connection timeout",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(
            UpdateDeviceFirmwareRequest(device_ip=device_ip)
        )

        assert result.success is False
        assert result.message == "Device is offline"
        assert result.error == "Connection timeout"

    async def test_it_propagates_network_errors(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(
            side_effect=ConnectionError("Network unreachable")
        )

        with pytest.raises(ConnectionError, match="Network unreachable"):
            await use_case.execute(UpdateDeviceFirmwareRequest(device_ip=device_ip))

    async def test_it_updates_multiple_devices_in_bulk(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        devices = [
            DiscoveredDevice(
                ip="192.168.1.100",
                status=Status.DETECTED,
                device_id="shelly1-test",
                device_type="SHSW-1",
                firmware_version="1.13.0",
                has_update=True,
            ),
            DiscoveredDevice(
                ip="192.168.1.101",
                status=Status.DETECTED,
                device_id="shelly2-test",
                device_type="SHSW-1",
                firmware_version="1.14.0",
                has_update=False,
            ),
            DiscoveredDevice(
                ip="192.168.1.102",
                status=Status.DETECTED,
                device_id="shelly3-test",
                device_type="SHSW-1",
                firmware_version="1.13.0",
                has_update=True,
            ),
        ]
        expected_results = [
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.100",
                message="Update successful",
            ),
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.102",
                message="Update successful",
            ),
        ]
        mock_device_gateway.discover_device = AsyncMock(side_effect=devices)
        mock_device_gateway.execute_action = AsyncMock(side_effect=expected_results)

        results = await use_case.execute_bulk(
            BulkUpdateDeviceFirmwareRequest(device_ips=device_ips)
        )

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False  # Device with no update available
        assert results[2].success is True

    async def test_it_updates_bulk_with_beta_channel(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        devices = [
            DiscoveredDevice(
                ip="192.168.1.100",
                status=Status.DETECTED,
                device_id="shelly1-test",
                device_type="SHSW-1",
                firmware_version="1.13.0",
                has_update=True,
            ),
            DiscoveredDevice(
                ip="192.168.1.101",
                status=Status.DETECTED,
                device_id="shelly2-test",
                device_type="SHSW-1",
                firmware_version="1.13.0",
                has_update=True,
            ),
        ]
        expected_results = [
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.100",
                message="Beta update successful",
            ),
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.101",
                message="Beta update successful",
            ),
        ]
        mock_device_gateway.discover_device = AsyncMock(side_effect=devices)
        mock_device_gateway.execute_action = AsyncMock(side_effect=expected_results)

        results = await use_case.execute_bulk(
            BulkUpdateDeviceFirmwareRequest(
                device_ips=device_ips, channel=UpdateChannel.BETA
            )
        )

        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_device_gateway.execute_action.call_count == 2

    async def test_it_includes_update_response_data(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        expected_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Firmware update completed",
            data={
                "old_version": "1.13.0",
                "new_version": "1.14.0",
                "update_duration": 120,
                "device_type": "SHPM-1",
            },
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=expected_result)

        result = await use_case.execute(
            UpdateDeviceFirmwareRequest(device_ip=device_ip)
        )

        assert result.success is True
        assert result.data is not None
        assert result.data["old_version"] == "1.13.0"
        assert result.data["new_version"] == "1.14.0"
        assert result.data["update_duration"] == 120

    # Validation tests (merged from DeviceUpdateService tests)
    async def test_it_validates_device_exists_before_update(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        with pytest.raises(
            DeviceValidationError, match="Device 192.168.1.100 not found"
        ):
            await use_case.execute(UpdateDeviceFirmwareRequest(device_ip=device_ip))

        mock_device_gateway.execute_action.assert_not_called()

    async def test_it_validates_update_available_unless_forced(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.14.0",
            has_update=False,
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        with pytest.raises(DeviceValidationError, match="has no available updates"):
            await use_case.execute(UpdateDeviceFirmwareRequest(device_ip=device_ip))

        mock_device_gateway.execute_action.assert_not_called()

    async def test_it_allows_forced_update_when_no_update_available(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.14.0",
            has_update=False,
        )
        action_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Forced update successful",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result = await use_case.execute(
            UpdateDeviceFirmwareRequest(device_ip=device_ip, force=True)
        )

        assert result.success is True

    async def test_it_validates_device_status_for_update(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.UNREACHABLE,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        with pytest.raises(
            DeviceValidationError, match="is not in valid state for update"
        ):
            await use_case.execute(UpdateDeviceFirmwareRequest(device_ip=device_ip))

        mock_device_gateway.execute_action.assert_not_called()

    async def test_it_rejects_auth_required_devices(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.AUTH_REQUIRED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)

        with pytest.raises(
            DeviceValidationError, match="is not in valid state for update"
        ):
            await use_case.execute(UpdateDeviceFirmwareRequest(device_ip=device_ip))

        mock_device_gateway.execute_action.assert_not_called()

    async def test_it_updates_with_all_channels(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"
        device = DiscoveredDevice(
            ip=device_ip,
            status=Status.DETECTED,
            device_id="shelly1-test",
            device_type="SHSW-1",
            firmware_version="1.13.0",
            has_update=True,
        )
        action_result = ActionResult(
            success=True,
            action_type="update",
            device_ip=device_ip,
            message="Update successful",
        )
        mock_device_gateway.discover_device = AsyncMock(return_value=device)
        mock_device_gateway.execute_action = AsyncMock(return_value=action_result)

        result_stable = await use_case.execute(
            UpdateDeviceFirmwareRequest(
                device_ip=device_ip, channel=UpdateChannel.STABLE
            )
        )
        result_beta = await use_case.execute(
            UpdateDeviceFirmwareRequest(device_ip=device_ip, channel=UpdateChannel.BETA)
        )

        assert result_stable.success is True
        assert result_beta.success is True
        assert mock_device_gateway.execute_action.call_count == 2
