"""
Device scanning use case.
"""

import asyncio
import ipaddress
from datetime import datetime

from ..domain.entities.discovered_device import DiscoveredDevice
from ..domain.entities.exceptions import DeviceValidationError, ValidationError
from ..domain.enums.enums import Status
from ..domain.value_objects.scan_request import ScanRequest
from ..gateways.configuration import ConfigurationGateway
from ..gateways.device import DeviceGateway


class ScanDevicesUseCase:

    def __init__(
        self, device_gateway: DeviceGateway, config_gateway: ConfigurationGateway
    ):
        self._device_gateway = device_gateway
        self._config_gateway = config_gateway

    async def execute(self, request: ScanRequest) -> list[DiscoveredDevice]:
        """
        Execute device scanning use case.

        Args:
            request: ScanRequest containing scan parameters

        Returns:
            List of discovered DiscoveredDevice objects

        Raises:
            ValidationError: If request validation fails
        """
        self._validate_scan_request(request)

        ips = await self._get_scan_ips(request)

        if not ips:
            return []

        semaphore = asyncio.Semaphore(request.max_workers)
        tasks = [self._scan_single_device(ip, request.timeout, semaphore) for ip in ips]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        discovered_devices = []
        for result in results:
            if isinstance(result, DiscoveredDevice) and result.status in [
                Status.DETECTED,
                Status.UPDATE_AVAILABLE,
                Status.NO_UPDATE_NEEDED,
            ]:
                discovered_devices.append(result)

        return discovered_devices

    def _validate_scan_request(self, request: ScanRequest) -> None:
        if request.use_predefined:
            return

        if not request.start_ip or not request.end_ip:
            raise ValidationError(
                "start_end_ips",
                "start_ip and end_ip required when not using predefined IPs",
            )

        if not self._validate_ip_address(request.start_ip):
            raise ValidationError(
                "start_ip",
                request.start_ip,
                f"Invalid start IP address: {request.start_ip}",
            )

        if not self._validate_ip_address(request.end_ip):
            raise ValidationError(
                "end_ip", request.end_ip, f"Invalid end IP address: {request.end_ip}"
            )

        if not self._validate_scan_range(request.start_ip, request.end_ip):
            raise ValidationError(
                "ip_range",
                f"{request.start_ip}-{request.end_ip}",
                "Start IP must be less than or equal to end IP",
            )

    async def _get_scan_ips(self, request: ScanRequest) -> list[str]:
        if request.use_predefined:
            return await self._config_gateway.get_predefined_ips()
        else:
            if request.start_ip is None or request.end_ip is None:
                raise ValueError(
                    "Start IP and end IP must be provided when not using predefined IPs"
                )
            return self._generate_ip_range(request.start_ip, request.end_ip)

    async def _scan_single_device(
        self, ip: str, timeout: float, semaphore: asyncio.Semaphore
    ) -> DiscoveredDevice | None:
        async with semaphore:
            try:
                device = await self._discover_device(ip, timeout)
                return device
            except Exception:
                return DiscoveredDevice(
                    ip=ip,
                    status=Status.ERROR,
                    last_seen=datetime.now(),
                    error_message="Device scan failed",
                )

    def _generate_ip_range(self, start_ip: str, end_ip: str) -> list[str]:
        try:
            start = ipaddress.IPv4Address(start_ip)
            end = ipaddress.IPv4Address(end_ip)

            if start > end:
                raise ValueError("Start IP must be less than or equal to end IP")

            return [
                str(ipaddress.IPv4Address(ip)) for ip in range(int(start), int(end) + 1)
            ]

        except ipaddress.AddressValueError as e:
            raise ValidationError(
                "ip_format", str(e), f"Invalid IP address format: {e}"
            ) from e

    # Private validation methods (merged from ValidationService)
    def _validate_ip_address(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ipaddress.AddressValueError:
            return False

    def _validate_device_credentials(
        self, username: str | None, password: str | None
    ) -> bool:
        """Validate device credentials."""
        if (username is None) != (password is None):
            return False

        if username and len(username) < 1:
            return False

        if password and len(password) < 1:
            return False

        return True

    def _validate_scan_range(self, start_ip: str, end_ip: str) -> bool:
        """Validate IP scan range."""
        try:
            start = ipaddress.IPv4Address(start_ip)
            end = ipaddress.IPv4Address(end_ip)
            return start <= end
        except ipaddress.AddressValueError:
            return False

    # Private device discovery methods (merged from DeviceDiscoveryService)
    async def _discover_device(
        self, ip: str, timeout: float = 3.0
    ) -> DiscoveredDevice | None:
        """
        Discover a device with business logic validation.

        Args:
            ip: Device IP address
            timeout: Discovery timeout

        Returns:
            DiscoveredDevice if found and valid, None otherwise

        Raises:
            DeviceValidationError: If device validation fails
        """
        try:
            device = await self._device_gateway.discover_device(ip)

            if device:
                self._validate_discovered_device(device)
                self._apply_device_status_rules(device)

            return device

        except Exception as e:
            raise DeviceValidationError(
                ip, f"Failed to discover device at {ip}: {str(e)}"
            ) from e

    def _validate_discovered_device(self, device: DiscoveredDevice) -> None:
        """Validate discovered device properties."""
        if not device.device_type:
            raise DeviceValidationError(
                device.ip, f"Device {device.ip} has no device type"
            )

        if not device.firmware_version:
            raise DeviceValidationError(
                device.ip, f"Device {device.ip} has no firmware version"
            )

    def _apply_device_status_rules(self, device: DiscoveredDevice) -> None:
        """Apply business rules to device status."""
        if device.auth_required and device.status in [
            Status.DETECTED,
            Status.UPDATE_AVAILABLE,
            Status.NO_UPDATE_NEEDED,
        ]:
            device.status = Status.AUTH_REQUIRED
