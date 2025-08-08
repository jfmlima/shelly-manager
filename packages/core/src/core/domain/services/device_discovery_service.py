"""
Domain service for device discovery business logic.
"""

from ...domain.entities.exceptions import DeviceValidationError
from ...gateways.device import DeviceGateway
from ..entities.shelly_device import ShellyDevice
from ..enums.enums import DeviceStatus


class DeviceDiscoveryService:

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def discover_device(
        self, ip: str, timeout: float = 3.0
    ) -> ShellyDevice | None:
        """
        Discover a device with business logic validation.

        Args:
            ip: Device IP address
            timeout: Discovery timeout

        Returns:
            ShellyDevice if found and valid, None otherwise

        Raises:
            DeviceValidationError: If device validation fails
        """
        try:
            device = await self._device_gateway.discover_device(ip, timeout)
            print(device)

            if device:
                self._validate_discovered_device(device)
                self._apply_device_status_rules(device)

            return device

        except Exception as e:
            raise DeviceValidationError(
                ip, f"Failed to discover device at {ip}: {str(e)}"
            ) from e

    def _validate_discovered_device(self, device: ShellyDevice) -> None:
        if not device.device_type:
            raise DeviceValidationError(
                device.ip, f"Device {device.ip} has no device type"
            )

        if not device.firmware_version:
            raise DeviceValidationError(
                device.ip, f"Device {device.ip} has no firmware version"
            )

    def _apply_device_status_rules(self, device: ShellyDevice) -> None:
        if device.auth_required and device.status == DeviceStatus.DETECTED:
            device.status = DeviceStatus.AUTH_REQUIRED
