"""
Device firmware update use case.
"""

import asyncio
from typing import Any

from ..domain.enums.enums import UpdateChannel
from ..domain.value_objects.action_result import ActionResult
from ..gateways.device import DeviceGateway


class UpdateDeviceFirmwareUseCase:

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self,
        device_ip: str,
        channel: UpdateChannel = UpdateChannel.STABLE,
        **kwargs: Any,
    ) -> ActionResult:
        """
        Update firmware on a single device.

        Args:
            device_ip: IP address of the device to update
            channel: Update channel (stable or beta)
            **kwargs: Additional parameters

        Returns:
            ActionResult indicating success or failure
        """
        parameters = {"channel": channel.value, **kwargs}

        return await self._device_gateway.execute_action(
            device_ip, "update", parameters
        )

    async def execute_bulk(
        self,
        device_ips: list[str],
        channel: UpdateChannel = UpdateChannel.STABLE,
        **kwargs: Any,
    ) -> list[ActionResult]:
        """
        Update firmware on multiple devices.

        Args:
            device_ips: List of IP addresses to update
            channel: Update channel (stable or beta)
            **kwargs: Additional parameters

        Returns:
            List of ActionResult objects
        """
        parameters = {"channel": channel.value, **kwargs}

        semaphore = asyncio.Semaphore(5)

        async def update_single(ip: str) -> ActionResult:
            async with semaphore:
                return await self._device_gateway.execute_action(
                    ip, "update", parameters
                )

        tasks = [update_single(ip) for ip in device_ips]
        return await asyncio.gather(*tasks, return_exceptions=False)
