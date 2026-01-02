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
        scan_request = ScanRequest(
            targets=request.targets,
            use_mdns=request.use_mdns,
            timeout=request.timeout,
            max_workers=request.workers,
        )
        scan_interactor = self._container.get_scan_interactor()
        return await scan_interactor.execute(scan_request)
