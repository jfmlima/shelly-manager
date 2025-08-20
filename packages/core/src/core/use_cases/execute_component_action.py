"""
Execute component action use case.
"""

from typing import Any

from ..domain.value_objects.action_result import ActionResult
from ..domain.value_objects.component_action_request import ComponentActionRequest
from ..gateways.device import DeviceGateway


class ExecuteComponentActionUseCase:
    """Unified use case for all component actions."""

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self, request: ComponentActionRequest, **kwargs: Any
    ) -> ActionResult:
        """Execute component action with validation.

        Args:
            request: Component action request containing device IP, component key, action, and parameters
            **kwargs: Additional keyword arguments (unused but kept for compatibility)

        Returns:
            ActionResult with success/failure details
        """
        return await self._device_gateway.execute_component_action(
            request.device_ip,
            request.component_key,
            request.action,
            request.parameters,
        )
