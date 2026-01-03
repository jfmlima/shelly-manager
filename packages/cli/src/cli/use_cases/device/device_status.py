"""
Device status checking use case for CLI operations.
"""

from typing import Any

from core.domain.value_objects.check_device_status_request import (
    CheckDeviceStatusRequest,
)
from rich.console import Console

from cli.dependencies.container import CLIContainer
from cli.entities import DeviceStatusRequest
from cli.presentation.styles import Messages

from ..common.device_discovery import DeviceDiscoveryRequest, DeviceDiscoveryUseCase
from ..common.progress_tracking import ProgressTracker
from ..common.result_formatting import ResultFormatter


class DeviceStatusUseCase:
    """
    Use case for checking status of Shelly devices.

    Handles the CLI orchestration for device status checking including:
    - Device discovery
    - Status checking with progress tracking
    - Error handling and result formatting
    """

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._device_discovery = DeviceDiscoveryUseCase(container)
        self._progress_tracker = ProgressTracker(console)
        self._result_formatter = ResultFormatter(console)

    async def execute(self, request: DeviceStatusRequest) -> list[Any]:
        """
        Execute device status checking operation.

        Args:
            request: Status request parameters

        Returns:
            List of status results

        Raises:
            ValueError: If no targets are specified
        """
        if not request.targets:
            raise ValueError(
                "You must specify at least one target (IP, range, or CIDR)"
            )

        device_ips = await self._get_device_ips(request)

        if not device_ips:
            return []

        return await self._check_device_status(device_ips, request)

    async def _get_device_ips(self, request: DeviceStatusRequest) -> list[str]:
        """Get device IPs by discovering/expanding targets."""
        discovery_request = DeviceDiscoveryRequest(
            targets=request.targets,
            timeout=request.timeout,
            workers=request.workers,
        )

        device_list = await self._device_discovery.discover_devices(discovery_request)
        return [d.ip for d in device_list]

    async def _check_device_status(
        self, device_ips: list[str], request: DeviceStatusRequest
    ) -> list[Any]:
        """Check status for all devices with progress tracking."""
        status_interactor = self._container.get_status_interactor()
        results: list[Any] = []

        async with self._progress_tracker.track_progress(
            "Checking device status...", total=len(device_ips)
        ) as task:
            for device_ip in device_ips:
                try:
                    status_request = CheckDeviceStatusRequest(
                        device_ip=device_ip, include_updates=request.include_updates
                    )
                    status_result = await status_interactor.execute(status_request)
                    results.append(status_result)
                except Exception as e:
                    if request.verbose:
                        self._console.print(Messages.device_error(device_ip, str(e)))
                    results.append(
                        {"ip": device_ip, "status": "error", "error": str(e)}
                    )

                task.advance()

        return results

    def display_results(self, results: list[Any]) -> None:
        """Display status results to console."""
        self._result_formatter.format_device_table(results)
