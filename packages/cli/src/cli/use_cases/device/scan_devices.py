"""
Device scanning use case for CLI operations.
"""

from typing import Any

from rich.console import Console

from cli.dependencies.container import CLIContainer
from cli.entities import DeviceScanRequest
from cli.presentation.styles import Messages

from ..common.device_discovery import DeviceDiscoveryRequest, DeviceDiscoveryUseCase
from ..common.progress_tracking import ProgressTracker
from ..common.result_formatting import ResultFormatter


class DeviceScanUseCase:
    """
    Use case for scanning and discovering Shelly devices.

    Handles the CLI orchestration for device scanning including:
    - Device discovery through various methods
    - Progress tracking
    - Result formatting and display
    """

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._device_discovery = DeviceDiscoveryUseCase(container)
        self._progress_tracker = ProgressTracker(console)
        self._result_formatter = ResultFormatter(console)

    async def execute(self, request: DeviceScanRequest) -> list[Any]:
        """
        Execute device scan operation.

        Args:
            request: Scan request parameters

        Returns:
            List of discovered devices
        """
        discovery_request = DeviceDiscoveryRequest(
            ip_ranges=request.ip_ranges,
            devices=request.devices,
            from_config=request.from_config,
            timeout=request.timeout,
            workers=request.workers,
            use_mdns=request.use_mdns,
        )

        async with self._progress_tracker.track_progress(
            request.task_description, total=None
        ) as task:
            devices_found = await self._device_discovery.discover_devices(
                discovery_request
            )
            task.update(f"Found {len(devices_found)} devices")

        return devices_found

    def display_results(
        self, devices_found: list[Any], show_table: bool = True
    ) -> None:
        """
        Display scan results to console.

        Args:
            devices_found: List of discovered devices
            show_table: Whether to show device table
        """
        if show_table:
            self._result_formatter.format_device_table(devices_found)

        if devices_found:
            self._console.print(
                f"\n{Messages.success(f'Found {len(devices_found)} devices')}"
            )
        else:
            self._console.print(f"\n{Messages.warning('No devices found')}")
