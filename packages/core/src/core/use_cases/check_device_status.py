"""
Device status use case.
"""

from ..domain.entities.shelly_device import ShellyDevice
from ..gateways.device import DeviceGateway


class CheckDeviceStatusUseCase:

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def execute(
        self, device_ip: str, include_updates: bool = True
    ) -> ShellyDevice | None:
        """
        Get comprehensive device status.

        Args:
            device_ip: IP address of the device
            include_updates: Whether to include update information

        Returns:
            ShellyDevice with status information or None if not found
        """
        return await self._device_gateway.get_device_status(device_ip, include_updates)
