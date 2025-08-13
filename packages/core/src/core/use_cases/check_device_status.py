"""
Device status use case.
"""

from ..domain.entities.shelly_device import ShellyDevice
from ..domain.value_objects.check_device_status_request import CheckDeviceStatusRequest
from ..gateways.device import DeviceGateway


class CheckDeviceStatusUseCase:

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def execute(self, request: CheckDeviceStatusRequest) -> ShellyDevice | None:
        """
        Get comprehensive device status.

        Args:
            request: CheckDeviceStatusRequest with validated IP and parameters

        Returns:
            ShellyDevice with status information or None if not found
        """
        return await self._device_gateway.get_device_status(
            request.device_ip, request.include_updates
        )
