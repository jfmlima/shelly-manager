"""
Device reboot use case.
"""

from typing import Any

from ..domain.value_objects.action_result import ActionResult
from ..domain.value_objects.reboot_device_request import RebootDeviceRequest
from ..gateways.device import DeviceGateway


class RebootDeviceUseCase:

    def __init__(self, device_gateway: DeviceGateway) -> None:
        self._device_gateway = device_gateway

    async def execute(
        self, request: RebootDeviceRequest, **kwargs: Any
    ) -> ActionResult:
        """
        Reboot a single device.

        Args:
            request: RebootDeviceRequest with validated IP and reboot parameters
            **kwargs: Additional parameters

        Returns:
            ActionResult indicating success or failure
        """
        # Build parameters from request fields
        params = {}
        if request.delay is not None:
            params["delay"] = request.delay
        if request.force is not None:
            params["force"] = request.force
        if request.username is not None:
            params["username"] = request.username
        if request.password is not None:
            params["password"] = request.password
        if request.timeout is not None:
            params["timeout"] = request.timeout
        
        # Add any additional kwargs
        params.update(kwargs)
        
        return await self._device_gateway.execute_action(
            request.device_ip, "reboot", params
        )
