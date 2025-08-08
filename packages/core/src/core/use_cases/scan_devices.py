"""
Device scanning use case.
"""

import asyncio
import ipaddress
from datetime import datetime

from ..domain.entities.exceptions import ValidationError
from ..domain.entities.shelly_device import ShellyDevice
from ..domain.enums.enums import DeviceStatus
from ..domain.services.device_discovery_service import DeviceDiscoveryService
from ..domain.services.validation_service import ValidationService
from ..domain.value_objects.scan_request import ScanRequest
from ..gateways.configuration import ConfigurationGateway
from ..gateways.device import DeviceGateway


class ScanDevicesUseCase:

    def __init__(
        self, device_gateway: DeviceGateway, config_gateway: ConfigurationGateway
    ):
        self._device_gateway = device_gateway
        self._config_gateway = config_gateway
        self._discovery_service = DeviceDiscoveryService(device_gateway)
        self._validation_service = ValidationService()

    async def execute(self, request: ScanRequest) -> list[ShellyDevice]:
        """
        Execute device scanning use case.

        Args:
            request: ScanRequest containing scan parameters

        Returns:
            List of discovered ShellyDevice objects

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
            if (
                isinstance(result, ShellyDevice)
                and result.status == DeviceStatus.DETECTED
            ):
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

        if not self._validation_service.validate_ip_address(request.start_ip):
            raise ValidationError(
                "start_ip",
                request.start_ip,
                f"Invalid start IP address: {request.start_ip}",
            )

        if not self._validation_service.validate_ip_address(request.end_ip):
            raise ValidationError(
                "end_ip", request.end_ip, f"Invalid end IP address: {request.end_ip}"
            )

        if not self._validation_service.validate_scan_range(
            request.start_ip, request.end_ip
        ):
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
    ) -> ShellyDevice | None:
        async with semaphore:
            try:
                device = await self._discovery_service.discover_device(ip, timeout)
                return device
            except Exception:
                return ShellyDevice(
                    ip=ip,
                    status=DeviceStatus.ERROR,
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
