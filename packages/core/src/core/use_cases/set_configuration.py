"""
Set device configuration use case.
"""

from typing import Any

from ..domain.value_objects.set_configuration_request import SetConfigurationRequest
from ..gateways.device import DeviceGateway


class SetConfigurationUseCase:
    """Use case for setting device configuration."""

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self, request: SetConfigurationRequest, **kwargs: Any
    ) -> dict[str, Any]:
        """Set device configuration.

        Args:
            request: Set configuration request containing device IP and configuration
            **kwargs: Additional keyword arguments (unused but kept for compatibility)

        Returns:
            Dictionary with success status and message

        Raises:
            ValueError: If configuration data is empty
            Exception: Gateway exceptions are propagated (ConnectionError, etc.)
        """
        if not request.config:
            raise ValueError("Configuration data required")

        success = await self._device_gateway.set_device_config(
            request.device_ip, request.config
        )

        return {
            "success": success,
            "message": (
                "Configuration updated successfully"
                if success
                else "Failed to update configuration"
            ),
        }
