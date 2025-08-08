"""
Common device discovery patterns for CLI operations.
"""

from typing import Any

from core.domain.value_objects.scan_request import ScanRequest

from cli.dependencies.container import CLIContainer
from cli.entities import DeviceDiscoveryRequest


class DeviceDiscoveryUseCase:
    def __init__(self, container: CLIContainer):
        self._container = container

    async def discover_devices(self, request: DeviceDiscoveryRequest) -> list[Any]:
        """
        Discover devices based on the provided request parameters.

        Returns:
            List of discovered devices
        """
        scan_request = self._create_scan_request(request)
        scan_interactor = self._container.get_scan_interactor()
        return await scan_interactor.execute(scan_request)

    def _create_scan_request(self, request: DeviceDiscoveryRequest) -> ScanRequest:
        """Create a ScanRequest from the discovery request."""
        if request.from_config:
            return ScanRequest(
                use_predefined=True,
                start_ip=None,
                end_ip=None,
                timeout=request.timeout,
                max_workers=request.workers,
            )

        if request.ip_ranges:
            from cli.commands.common import parse_ip_range

            start_ip, end_ip = parse_ip_range(request.ip_ranges[0])
            return ScanRequest(
                start_ip=start_ip,
                end_ip=end_ip,
                use_predefined=False,
                timeout=request.timeout,
                max_workers=request.workers,
            )

        if request.devices:
            from cli.commands.common import parse_ip_range

            if len(request.devices) == 1:
                start_ip, end_ip = parse_ip_range(request.devices[0])
            else:
                start_ip, end_ip = request.devices[0], request.devices[-1]

            return ScanRequest(
                start_ip=start_ip,
                end_ip=end_ip,
                use_predefined=False,
                timeout=request.timeout,
                max_workers=request.workers,
            )

        return ScanRequest(
            use_predefined=True,
            start_ip=None,
            end_ip=None,
            timeout=request.timeout,
            max_workers=request.workers,
        )
