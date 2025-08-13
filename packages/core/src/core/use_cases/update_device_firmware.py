"""
Device firmware update use case.
"""

import asyncio
from typing import Any

from core.settings import settings

from ..domain.entities.exceptions import DeviceValidationError
from ..domain.enums.enums import DeviceStatus, UpdateChannel
from ..domain.value_objects.action_result import ActionResult
from ..gateways.device import DeviceGateway


class UpdateDeviceFirmwareUseCase:

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self,
        device_ip: str,
        channel: UpdateChannel = UpdateChannel.STABLE,
        force: bool = False,
        **kwargs: Any,
    ) -> ActionResult:
        """
        Update firmware on a single device with validation.

        Args:
            device_ip: IP address of the device to update
            channel: Update channel (stable or beta)
            force: Force update even if not needed
            **kwargs: Additional parameters

        Returns:
            ActionResult indicating success or failure

        Raises:
            DeviceValidationError: If update validation fails
        """
        # Validate device before update (merged from DeviceUpdateService)
        device = await self._device_gateway.get_device_status(device_ip)

        if not device:
            raise DeviceValidationError(device_ip, f"Device {device_ip} not found")

        if not force and not device.has_update:
            raise DeviceValidationError(
                device_ip, f"Device {device_ip} has no available updates"
            )

        if device.status != DeviceStatus.DETECTED:
            raise DeviceValidationError(
                device_ip, f"Device {device_ip} is not in valid state for update"
            )

        parameters = {"channel": channel.value, **kwargs}

        return await self._device_gateway.execute_action(
            device_ip, "update", parameters
        )

    async def execute_bulk(
        self,
        device_ips: list[str],
        channel: UpdateChannel = UpdateChannel.STABLE,
        force: bool = False,
        **kwargs: Any,
    ) -> list[ActionResult]:
        """
        Update firmware on multiple devices.

        Args:
            device_ips: List of IP addresses to update
            channel: Update channel (stable or beta)
            force: Force update even if not needed
            **kwargs: Additional parameters

        Returns:
            List of ActionResult objects
        """
        # Determine effective concurrency: request override via kwargs or settings
        override_workers = kwargs.get("max_workers")
        max_workers = (
            int(override_workers)
            if override_workers is not None
            else int(settings.network.max_workers)
        )
        if max_workers < 1:
            max_workers = 1
        semaphore = asyncio.Semaphore(max_workers)

        async def update_single(ip: str) -> ActionResult:
            async with semaphore:
                try:
                    return await self.execute(ip, channel, force, **kwargs)
                except DeviceValidationError as e:
                    # Return failed result instead of raising exception for bulk operations
                    from ..domain.value_objects.action_result import ActionResult
                    return ActionResult(
                        success=False, 
                        action_type="update",
                        device_ip=ip,
                        message=str(e), 
                        data={"ip": ip}
                    )

        tasks = [update_single(ip) for ip in device_ips]
        return await asyncio.gather(*tasks, return_exceptions=False)
