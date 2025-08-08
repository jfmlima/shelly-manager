"""
Set device configuration use case.
"""

from typing import Any

from ..gateways.device import DeviceGateway


class SetConfigurationUseCase:

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def execute(self, device_ip: str, config: dict[str, Any]) -> dict[str, Any]:
        """
        Set device configuration.

        Args:
            device_ip: IP address of the device
            config: Configuration to set

        Returns:
            Result dictionary with success status and message

        Raises:
            ValueError: If configuration data is invalid
        """
        if not config:
            raise ValueError("Configuration data required")

        success = await self._device_gateway.set_device_config(device_ip, config)
        return {
            "success": success,
            "message": (
                "Configuration updated successfully"
                if success
                else "Failed to update configuration"
            ),
        }
