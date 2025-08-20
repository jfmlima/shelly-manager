"""
Get device configuration use case.
"""

from typing import Any

from ..domain.value_objects.device_configuration_request import (
    DeviceConfigurationRequest,
)
from ..gateways.device import DeviceGateway


class GetConfigurationUseCase:
    """Use case for getting device configuration."""

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self, request: DeviceConfigurationRequest, **kwargs: Any
    ) -> dict[str, Any]:
        """Get device configuration.

        Args:
            request: Device configuration request containing device IP
            **kwargs: Additional keyword arguments (unused but kept for compatibility)

        Returns:
            Device configuration dictionary

        Raises:
            ValueError: If configuration could not be retrieved from device
            Exception: Gateway exceptions are propagated (ConnectionError, etc.)
        """
        config = await self._device_gateway.get_device_config(request.device_ip)

        if config is None:
            raise ValueError(
                f"Could not retrieve configuration for device: {request.device_ip}"
            )

        return config
