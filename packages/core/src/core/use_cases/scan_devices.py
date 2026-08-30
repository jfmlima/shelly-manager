import asyncio
import logging
from datetime import datetime
from typing import Any

from ..domain.entities.discovered_device import DiscoveredDevice
from ..domain.entities.exceptions import (
    ConfigurationError,
    DeviceValidationError,
    ValidationError,
)
from ..domain.enums.enums import Status, UpdateChannel
from ..domain.value_objects.firmware_release import FirmwareRelease
from ..domain.value_objects.scan_request import ScanRequest
from ..gateways.device import DeviceGateway
from ..gateways.firmware import FirmwareGateway
from ..gateways.network import MDNSGateway

logger = logging.getLogger(__name__)


class ScanDevicesUseCase:

    def __init__(
        self,
        device_gateway: DeviceGateway,
        mdns_client: MDNSGateway | None = None,
        auth_state_cache: Any | None = None,
        firmware_gateway: FirmwareGateway | None = None,
    ):
        self._device_gateway = device_gateway
        self._mdns_client = mdns_client
        self._auth_state_cache = auth_state_cache
        self._firmware_gateway = firmware_gateway

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

        for result in results:
            if isinstance(result, ConfigurationError):
                raise result

        discovered_devices = []
        for result in results:
            if isinstance(result, DiscoveredDevice) and result.status in [
                Status.DETECTED,
                Status.UPDATE_AVAILABLE,
                Status.NO_UPDATE_NEEDED,
                Status.AUTH_REQUIRED,
            ]:
                discovered_devices.append(result)

        await self._settle_update_status(discovered_devices)

        return discovered_devices

    async def _settle_update_status(self, devices: list[DiscoveredDevice]) -> None:
        """Answer stalled update checks from the manager's own index lookup.

        A device that cannot reach Shelly's cloud fails its own update check
        and stays DETECTED, which the UI reads as an open question even though
        the manager can still serve it firmware locally. The index the manager
        queries here is the same one local updates install from, so the badge
        and the via-manager path cannot disagree. Stable only: it is what an
        unqualified "update available" means everywhere else in the app.
        """
        firmware_gateway = self._firmware_gateway
        if firmware_gateway is None:
            return

        pending: dict[str, list[DiscoveredDevice]] = {}
        for device in devices:
            if device.status == Status.DETECTED and device.app_name:
                pending.setdefault(device.app_name, []).append(device)
        if not pending:
            return

        apps = sorted(pending)
        lookups = await asyncio.gather(
            *(self._lookup_release(firmware_gateway, app) for app in apps)
        )

        for app, release in zip(apps, lookups, strict=True):
            if release is None:
                continue
            for device in pending[app]:
                if release.is_installed_on(device.firmware_version):
                    device.status = Status.NO_UPDATE_NEEDED
                else:
                    device.status = Status.UPDATE_AVAILABLE
                    device.available_firmware_version = release.version
                    device.available_firmware_channel = UpdateChannel.STABLE

    async def _lookup_release(
        self, firmware_gateway: FirmwareGateway, app_name: str
    ) -> FirmwareRelease | None:
        try:
            return await firmware_gateway.get_latest(app_name)
        except Exception as e:
            logger.warning("Firmware index lookup failed for app %s: %s", app_name, e)
            return None

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
            except ConfigurationError:
                raise
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
            device = await self._device_gateway.discover_device(ip, timeout=timeout)

            if device:
                self._validate_discovered_device(device)
                self._apply_device_status_rules(device)

            return device

        except ConfigurationError:
            raise
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
        if device.auth_required and device.status == Status.DETECTED:
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
