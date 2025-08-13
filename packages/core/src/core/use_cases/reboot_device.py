"""
Device reboot use case.
"""

from typing import Any

from ..domain.value_objects.action_result import ActionResult
from ..domain.value_objects.reboot_device_request import RebootDeviceRequest
from ..gateways.device import DeviceGateway


class RebootDeviceUseCase:

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self, request: RebootDeviceRequest, **kwargs: Any
    ) -> ActionResult:
        """
        Reboot a single device.

        Args:
            request: RebootDeviceRequest with validated IP
            **kwargs: Additional parameters

        Returns:
            ActionResult indicating success or failure
        """
        return await self._device_gateway.execute_action(
            request.device_ip, "reboot", kwargs
        )
