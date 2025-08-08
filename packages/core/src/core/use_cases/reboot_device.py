"""
Device reboot use case.
"""

from typing import Any

from ..domain.value_objects.action_result import ActionResult
from ..gateways.device import DeviceGateway


class RebootDeviceUseCase:

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(self, device_ip: str, **kwargs: Any) -> ActionResult:
        """
        Reboot a single device.

        Args:
            device_ip: IP address of the device to reboot
            **kwargs: Additional parameters

        Returns:
            ActionResult indicating success or failure
        """
        return await self._device_gateway.execute_action(device_ip, "reboot", kwargs)
