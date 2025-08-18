"""
Device status use case.
"""

from ..domain.entities.device_status import DeviceStatus
from ..domain.value_objects.check_device_status_request import CheckDeviceStatusRequest
from ..gateways.device import DeviceGateway


class CheckDeviceStatusUseCase:

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def execute(self, request: CheckDeviceStatusRequest) -> DeviceStatus | None:
        """
        Get comprehensive device components and status.

        Args:
            request: CheckDeviceStatusRequest with validated IP and parameters

        Returns:
            DeviceStatus with all component information or None if not found
        """
        return await self._device_gateway.get_device_status(request.device_ip)
