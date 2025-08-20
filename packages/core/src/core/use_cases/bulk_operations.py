"""
Bulk operations use case for executing actions on multiple devices.
"""

import asyncio

from ..domain.entities.device_status import DeviceStatus
from ..domain.entities.discovered_device import DiscoveredDevice
from ..domain.entities.exceptions import BulkOperationError
from ..domain.enums.enums import Status
from ..domain.value_objects.action_result import ActionResult
from ..domain.value_objects.bulk_scan_request import BulkScanRequest
from ..gateways.device import DeviceGateway


class BulkOperationsUseCase:

    def __init__(
        self,
        device_gateway: DeviceGateway,
    ):
        self._device_gateway = device_gateway

    async def execute_bulk_scan(
        self, request: BulkScanRequest
    ) -> list[DiscoveredDevice]:
        """
        Scan multiple IP addresses for devices.

        Args:
            request: BulkScanRequest with validated IPs and timeout

        Returns:
            List of discovered devices
        """
        results = []

        try:
            tasks = [self._device_gateway.discover_device(ip) for ip in request.ips]

            devices = await asyncio.gather(*tasks, return_exceptions=True)

            for device in devices:
                if (
                    isinstance(device, DiscoveredDevice)
                    and device.status == Status.DETECTED
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
                device_ips, "shelly", "Update", {"channel": channel}
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
                device_ips, "shelly", "Reboot", {}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_reboot", device_ips, f"Bulk reboot failed: {str(e)}"
            ) from e

    async def execute_bulk_factory_reset(
        self, device_ips: list[str]
    ) -> list[ActionResult]:
        """
        Factory reset multiple devices.

        Args:
            device_ips: List of device IP addresses

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "shelly", "FactoryReset", {}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_factory_reset", device_ips, f"Bulk factory reset failed: {str(e)}"
            ) from e

    async def get_bulk_status(
        self, device_ips: list[str], include_updates: bool = True
    ) -> list[DeviceStatus]:
        """
        Get status of multiple devices.

        Args:
            device_ips: List of device IP addresses
            include_updates: Include update information (parameter kept for compatibility but not used)

        Returns:
            List of device statuses
        """
        results = []

        for ip in device_ips:
            try:
                device = await self._device_gateway.get_device_status(ip)
                if device:
                    results.append(device)
            except Exception as e:
                print(f"Error getting status for {ip}: {str(e)}")

        return results
