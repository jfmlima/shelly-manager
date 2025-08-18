from unittest.mock import AsyncMock

import pytest
from core.domain.value_objects.bulk_scan_request import BulkScanRequest
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.entities.exceptions import BulkOperationError
from core.domain.enums.enums import Status
from core.domain.value_objects.action_result import ActionResult
from core.use_cases.bulk_operations import BulkOperationsUseCase


class TestBulkOperationsUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return BulkOperationsUseCase(device_gateway=mock_device_gateway)

    async def test_it_scans_multiple_devices_successfully(
        self, use_case, mock_device_gateway
    ):
        ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        devices = [
            DiscoveredDevice(
                ip="192.168.1.100", status=Status.DETECTED, device_id="device1"
            ),
            DiscoveredDevice(
                ip="192.168.1.101", status=Status.DETECTED, device_id="device2"
            ),
            None,
        ]
        mock_device_gateway.discover_device = AsyncMock()
        mock_device_gateway.discover_device.side_effect = devices

        result = await use_case.execute_bulk_scan(BulkScanRequest(ips=ips))

        assert len(result) == 2
        assert result[0].ip == "192.168.1.100"
        assert result[1].ip == "192.168.1.101"
        assert all(device.status == Status.DETECTED for device in result)

    async def test_it_handles_bulk_scan_with_no_devices(
        self, use_case, mock_device_gateway
    ):
        ips = ["192.168.1.100", "192.168.1.101"]
        mock_device_gateway.discover_device = AsyncMock(return_value=None)

        result = await use_case.execute_bulk_scan(BulkScanRequest(ips=ips))

        assert result == []
        assert mock_device_gateway.discover_device.call_count == 2

    async def test_it_filters_non_detected_devices_in_bulk_scan(
        self, use_case, mock_device_gateway
    ):
        ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        devices = [
            DiscoveredDevice(
                ip="192.168.1.100", status=Status.DETECTED, device_id="device1"
            ),
            DiscoveredDevice(
                ip="192.168.1.101", status=Status.UNREACHABLE, device_id="device2"
            ),
            DiscoveredDevice(
                ip="192.168.1.102",
                status=Status.AUTH_REQUIRED,
                device_id="device3",
            ),
        ]
        mock_device_gateway.discover_device = AsyncMock()
        mock_device_gateway.discover_device.side_effect = devices

        result = await use_case.execute_bulk_scan(BulkScanRequest(ips=ips))

        assert len(result) == 1
        assert result[0].ip == "192.168.1.100"
        assert result[0].status == Status.DETECTED

    async def test_it_handles_scan_failures_gracefully(
        self, use_case, mock_device_gateway
    ):
        ips = ["192.168.1.100"]
        mock_device_gateway.discover_device = AsyncMock(
            side_effect=Exception("Network error")
        )

        result = await use_case.execute_bulk_scan(BulkScanRequest(ips=ips))

        assert result == []

    async def test_it_updates_multiple_devices_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
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
                device_ip="192.168.1.101",
                message="Update successful",
            ),
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_update(device_ips, "stable")

        assert len(results) == 2
        assert all(result.success for result in results)
        mock_device_gateway.execute_bulk_action.assert_called_once_with(
            device_ips, "update", {"channel": "stable"}
        )

    async def test_it_updates_with_beta_channel(self, use_case, mock_device_gateway):
        device_ips = ["192.168.1.100"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="update",
                device_ip="192.168.1.100",
                message="Beta update successful",
            )
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_update(device_ips, "beta")

        assert len(results) == 1
        assert results[0].success is True
        mock_device_gateway.execute_bulk_action.assert_called_once_with(
            device_ips, "update", {"channel": "beta"}
        )

    async def test_it_raises_bulk_operation_error_on_update_failure(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            side_effect=Exception("Gateway error")
        )

        with pytest.raises(BulkOperationError, match="Bulk update failed"):
            await use_case.execute_bulk_update(device_ips)

    async def test_it_reboots_multiple_devices_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="reboot",
                device_ip="192.168.1.100",
                message="Reboot successful",
            ),
            ActionResult(
                success=True,
                action_type="reboot",
                device_ip="192.168.1.101",
                message="Reboot successful",
            ),
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_reboot(device_ips)

        assert len(results) == 2
        assert all(result.success for result in results)
        mock_device_gateway.execute_bulk_action.assert_called_once_with(
            device_ips, "reboot", {}
        )

    async def test_it_raises_bulk_operation_error_on_reboot_failure(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100"]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            side_effect=Exception("Gateway error")
        )

        with pytest.raises(BulkOperationError, match="Bulk reboot failed"):
            await use_case.execute_bulk_reboot(device_ips)

    async def test_it_sets_configuration_on_multiple_devices(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101"]
        config = {"name": "Bulk Updated Device"}
        expected_results = [
            ActionResult(
                success=True,
                action_type="config_set",
                device_ip="192.168.1.100",
                message="Config updated",
            ),
            ActionResult(
                success=True,
                action_type="config_set",
                device_ip="192.168.1.101",
                message="Config updated",
            ),
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_config_set(device_ips, config)

        assert len(results) == 2
        assert all(result.success for result in results)
        mock_device_gateway.execute_bulk_action.assert_called_once_with(
            device_ips, "config-set", {"config": config}
        )

    async def test_it_handles_mixed_results_in_bulk_operations(
        self, use_case, mock_device_gateway
    ):
        device_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        expected_results = [
            ActionResult(
                success=True,
                action_type="reboot",
                device_ip="192.168.1.100",
                message="Reboot successful",
            ),
            ActionResult(
                success=False,
                action_type="reboot",
                device_ip="192.168.1.101",
                message="Reboot failed",
                error="Device offline",
            ),
            ActionResult(
                success=True,
                action_type="reboot",
                device_ip="192.168.1.102",
                message="Reboot successful",
            ),
        ]
        mock_device_gateway.execute_bulk_action = AsyncMock(
            return_value=expected_results
        )

        results = await use_case.execute_bulk_reboot(device_ips)

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert results[1].error == "Device offline"

    async def test_it_handles_scan_exceptions_gracefully(
        self, use_case, mock_device_gateway
    ):
        ips = ["192.168.1.100", "192.168.1.101"]
        devices = [
            DiscoveredDevice(
                ip="192.168.1.100", status=Status.DETECTED, device_id="device1"
            ),
            Exception("Network error for second device"),
        ]
        mock_device_gateway.discover_device = AsyncMock()
        mock_device_gateway.discover_device.side_effect = devices

        result = await use_case.execute_bulk_scan(BulkScanRequest(ips=ips))

        assert len(result) == 1
        assert result[0].ip == "192.168.1.100"

    async def test_it_uses_custom_timeout_for_bulk_scan(
        self, use_case, mock_device_gateway
    ):
        ips = ["192.168.1.100"]
        devices = [
            DiscoveredDevice(
                ip="192.168.1.100", status=Status.DETECTED, device_id="device1"
            )
        ]
        mock_device_gateway.discover_device = AsyncMock()
        mock_device_gateway.discover_device.side_effect = devices

        result = await use_case.execute_bulk_scan(BulkScanRequest(ips=ips, timeout=10.0))

        assert len(result) == 1
        mock_device_gateway.discover_device.assert_called_with("192.168.1.100")

    async def test_it_handles_empty_device_list_for_bulk_operations(
        self, use_case, mock_device_gateway
    ):
        empty_ips = []
        mock_device_gateway.execute_bulk_action = AsyncMock(return_value=[])

        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            BulkScanRequest(ips=empty_ips)
        
        update_result = await use_case.execute_bulk_update(empty_ips)
        reboot_result = await use_case.execute_bulk_reboot(empty_ips)

        assert update_result == []
        assert reboot_result == []
