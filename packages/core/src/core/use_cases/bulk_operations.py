"""
Bulk operations use case for executing actions on multiple devices.
"""

import asyncio
from typing import Any

from ..domain.entities.exceptions import BulkOperationError
from ..domain.entities.shelly_device import ShellyDevice
from ..domain.enums.enums import DeviceStatus
from ..domain.value_objects.action_result import ActionResult
from ..domain.value_objects.bulk_scan_request import BulkScanRequest
from ..gateways.device import DeviceGateway


class BulkOperationsUseCase:

    def __init__(
        self,
        device_gateway: DeviceGateway,
    ):
        self._device_gateway = device_gateway

    async def execute_bulk_scan(self, request: BulkScanRequest) -> list[ShellyDevice]:
        """
        Scan multiple IP addresses for devices.

        Args:
            request: BulkScanRequest with validated IPs and timeout

        Returns:
            List of discovered devices
        """
        results = []

        try:
            tasks = [
                self._device_gateway.discover_device(ip, request.timeout)
                for ip in request.ips
            ]

            devices = await asyncio.gather(*tasks, return_exceptions=True)

            for device in devices:
                if (
                    isinstance(device, ShellyDevice)
                    and device.status == DeviceStatus.DETECTED
                ):
                    results.append(device)

        except Exception as e:
            raise BulkOperationError(
                "bulk_scan", request.ips, f"Bulk scan failed: {str(e)}"
            ) from e

        return results

    async def execute_bulk_update(
        self, device_ips: list[str], channel: str = "stable"
    ) -> list[ActionResult]:
        """
        Update firmware on multiple devices.

        Args:
            device_ips: List of device IP addresses
            channel: Update channel (stable/beta)

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "update", {"channel": channel}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_update", device_ips, f"Bulk update failed: {str(e)}"
            ) from e

    async def execute_bulk_reboot(self, device_ips: list[str]) -> list[ActionResult]:
        """
        Reboot multiple devices.

        Args:
            device_ips: List of device IP addresses

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "reboot", {}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_reboot", device_ips, f"Bulk reboot failed: {str(e)}"
            ) from e

    async def execute_bulk_config_set(
        self, device_ips: list[str], config: dict[str, Any]
    ) -> list[ActionResult]:
        """
        Set configuration on multiple devices.

        Args:
            device_ips: List of device IP addresses
            config: Configuration to set

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "config-set", {"config": config}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_config_set", device_ips, f"Bulk config set failed: {str(e)}"
            ) from e

    async def get_bulk_status(
        self, device_ips: list[str], include_updates: bool = True
    ) -> list[ShellyDevice]:
        """
        Get status of multiple devices.

        Args:
            device_ips: List of device IP addresses
            include_updates: Include update information

        Returns:
            List of device statuses
        """
        results = []

        for ip in device_ips:
            try:
                device = await self._device_gateway.get_device_status(
                    ip, include_updates
                )
                if device:
                    results.append(device)
            except Exception as e:
                print(f"Error getting status for {ip}: {str(e)}")

        return results
