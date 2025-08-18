"""
Device firmware update use case.
"""

import asyncio
from typing import Any

from core.settings import settings

from ..domain.entities.exceptions import DeviceValidationError
from ..domain.enums.enums import Status
from ..domain.value_objects.action_result import ActionResult
from ..domain.value_objects.bulk_update_device_firmware_request import (
    BulkUpdateDeviceFirmwareRequest,
)
from ..domain.value_objects.update_device_firmware_request import (
    UpdateDeviceFirmwareRequest,
)
from ..gateways.device import DeviceGateway


class UpdateDeviceFirmwareUseCase:

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self,
        request: UpdateDeviceFirmwareRequest,
        **kwargs: Any,
    ) -> ActionResult:
        """
        Update firmware on a single device with validation.

        Args:
            request: UpdateDeviceFirmwareRequest with validated IP and parameters
            **kwargs: Additional parameters

        Returns:
            ActionResult indicating success or failure

        Raises:
            DeviceValidationError: If update validation fails
        """
        device = await self._device_gateway.discover_device(request.device_ip)

        if not device:
            raise DeviceValidationError(
                request.device_ip, f"Device {request.device_ip} not found"
            )

        if not request.force and not device.has_update:
            raise DeviceValidationError(
                request.device_ip,
                f"Device {request.device_ip} has no available updates",
            )

        if device.status != Status.DETECTED:
            raise DeviceValidationError(
                request.device_ip,
                f"Device {request.device_ip} is not in valid state for update",
            )

        parameters = {"channel": request.channel.value, **kwargs}

        return await self._device_gateway.execute_action(
            request.device_ip, "update", parameters
        )

    async def execute_bulk(
        self,
        request: BulkUpdateDeviceFirmwareRequest,
        **kwargs: Any,
    ) -> list[ActionResult]:
        """
        Update firmware on multiple devices.

        Args:
            request: BulkUpdateDeviceFirmwareRequest with validated IPs and parameters
            **kwargs: Additional parameters

        Returns:
            List of ActionResult objects
        """
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
                    single_request = UpdateDeviceFirmwareRequest(
                        device_ip=ip, channel=request.channel, force=request.force
                    )
                    return await self.execute(single_request, **kwargs)
                except DeviceValidationError as e:
                    from ..domain.value_objects.action_result import ActionResult

                    return ActionResult(
                        success=False,
                        action_type="update",
                        device_ip=ip,
                        message=str(e),
                        data={"ip": ip},
                    )

        tasks = [update_single(ip) for ip in request.device_ips]
        return await asyncio.gather(*tasks, return_exceptions=False)
