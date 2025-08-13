"""
Get device configuration use case.
"""

from typing import Any

from ..domain.value_objects.device_configuration_request import (
    DeviceConfigurationRequest,
)
from ..gateways.device import DeviceGateway


class GetConfigurationUseCase:

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def execute(self, request: DeviceConfigurationRequest) -> dict[str, Any]:
        """
        Get device configuration.

        Args:
            request: DeviceConfigurationRequest with validated IP

        Returns:
            Configuration data

        Raises:
            ValueError: If configuration cannot be retrieved
        """
        result = await self._device_gateway.get_device_config(request.device_ip)
        if result is None:
            raise ValueError(
                f"Could not retrieve configuration for device: {request.device_ip}"
            )
        return result
