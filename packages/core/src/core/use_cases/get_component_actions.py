"""
Get component actions use case.
"""

from typing import Any

from ..domain.value_objects.get_component_actions_request import (
    GetComponentActionsRequest,
)
from ..gateways.device import DeviceGateway


class GetComponentActionsUseCase:
    """Get available actions for device components."""

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self, request: GetComponentActionsRequest, **kwargs: Any
    ) -> dict[str, list[str]]:
        """Get component actions grouped by component key.

        Args:
            request: Request containing device IP
            **kwargs: Additional keyword arguments (unused but kept for compatibility)

        Returns:
            Dictionary mapping component keys to available action method names
        """
        device_status = await self._device_gateway.get_device_status(request.device_ip)

        if not device_status:
            return {}

        return {
            component.key: component.available_actions
            for component in device_status.components
        }
