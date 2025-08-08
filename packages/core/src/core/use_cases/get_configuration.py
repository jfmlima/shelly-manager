"""
Get device configuration use case.
"""

from typing import Any

from ..gateways.device import DeviceGateway


class GetConfigurationUseCase:

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def execute(self, device_ip: str) -> dict[str, Any]:
        """
        Get device configuration.

        Args:
            device_ip: IP address of the device

        Returns:
            Configuration data

        Raises:
            ValueError: If configuration cannot be retrieved
        """
        result = await self._device_gateway.get_device_config(device_ip)
        if result is None:
            raise ValueError(
                f"Could not retrieve configuration for device: {device_ip}"
            )
        return result
