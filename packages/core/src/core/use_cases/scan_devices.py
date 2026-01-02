import asyncio
import logging
from datetime import datetime

from ..domain.entities.discovered_device import DiscoveredDevice
from ..domain.entities.exceptions import DeviceValidationError, ValidationError
from ..domain.enums.enums import Status
from ..domain.value_objects.scan_request import ScanRequest
from ..gateways.device import DeviceGateway
from ..gateways.network import MDNSGateway

logger = logging.getLogger(__name__)


class ScanDevicesUseCase:

    def __init__(
        self,
        device_gateway: DeviceGateway,
        mdns_client: MDNSGateway | None = None,
    ):
        self._device_gateway = device_gateway
        self._mdns_client = mdns_client

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
        """Validate scan request."""
        if request.use_mdns:
            return

        if not request.targets:
            raise ValidationError(
                "targets",
                "At least one target is required when not using mDNS",
            )

    async def _get_scan_ips(self, request: ScanRequest) -> list[str]:
        """Get list of IPs to scan based on request."""
        if request.use_mdns:
            return await self._discover_devices_via_mdns(request)

        from ..utils.target_parser import expand_targets

        return expand_targets(request.targets)

    async def _scan_single_device(
        self, ip: str, timeout: float, semaphore: asyncio.Semaphore
    ) -> DiscoveredDevice | None:
        async with semaphore:
            try:
                return await self._discover_device(ip, timeout)
            except Exception:
                return DiscoveredDevice(
                    ip=ip,
                    status=Status.ERROR,
                    last_seen=datetime.now(),
                    error_message="Device scan failed",
                )

    async def _discover_device(
        self, ip: str, timeout: float = 3.0
    ) -> DiscoveredDevice | None:
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
        if not device.device_type:
            raise DeviceValidationError(
                device.ip, f"Device {device.ip} has no device type"
            )

        if not device.firmware_version:
            raise DeviceValidationError(
                device.ip, f"Device {device.ip} has no firmware version"
            )

    def _apply_device_status_rules(self, device: DiscoveredDevice) -> None:
        if device.auth_required and device.status in [
            Status.DETECTED,
            Status.UPDATE_AVAILABLE,
            Status.NO_UPDATE_NEEDED,
        ]:
            device.status = Status.AUTH_REQUIRED

    async def _discover_devices_via_mdns(self, request: ScanRequest) -> list[str]:
        if self._mdns_client is None:
            logger.warning("mDNS discovery requested but no mDNS gateway available")
            return []

        try:
            logger.info("Starting mDNS device discovery...")
            discovered_ips = await self._mdns_client.discover_device_ips(
                timeout=request.timeout
            )
            logger.info(f"mDNS discovery found {len(discovered_ips)} potential devices")
            return discovered_ips

        except Exception as e:
            logger.error(f"mDNS discovery failed: {e}", exc_info=True)
            return []
