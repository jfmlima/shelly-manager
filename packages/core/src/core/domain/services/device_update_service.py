"""
Domain service for device update business logic.
"""

from ...domain.entities.exceptions import DeviceValidationError
from ...gateways.device import DeviceGateway
from ..enums.enums import DeviceStatus, UpdateChannel


class DeviceUpdateService:

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def update_device(
        self,
        device_ip: str,
        channel: UpdateChannel = UpdateChannel.STABLE,
        force: bool = False,
    ) -> bool:
        """
        Update device firmware with business logic.

        Args:
            device_ip: Device IP address
            channel: Update channel
            force: Force update even if not needed

        Returns:
            True if update successful

        Raises:
            DeviceValidationError: If update validation fails
        """
        device = await self._device_gateway.get_device_status(device_ip)

        if not device:
            raise DeviceValidationError(device_ip, f"Device {device_ip} not found")

        if not force and not device.has_update:
            raise DeviceValidationError(
                device_ip, f"Device {device_ip} has no available updates"
            )

        if device.status != DeviceStatus.DETECTED:
            raise DeviceValidationError(
                device_ip, f"Device {device_ip} is not in valid state for update"
            )

        result = await self._device_gateway.execute_action(
            device_ip, "update", {"channel": channel.value}
        )

        return result.success
