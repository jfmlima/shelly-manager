"""
Device scanning use case for CLI operations.
"""

from typing import Any

from core.domain.enums.enums import Status
from rich.console import Console
from rich.markup import escape

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
            The devices found, followed by the addresses that did not answer
            or failed when the request asks for them
        """
        discovery_request = DeviceDiscoveryRequest(
            targets=request.targets,
            timeout=request.timeout,
            workers=request.workers,
            use_mdns=request.use_mdns,
            include_failed=request.include_failed,
        )

        async with self._progress_tracker.track_progress(
            request.task_description, total=None
        ) as task:
            results = await self._device_discovery.discover_devices(discovery_request)
            devices, _ = _split_failures(results)
            task.update(f"Found {len(devices)} devices")

        return results

    def display_results(
        self,
        devices_found: list[Any],
        show_table: bool = True,
        include_beta: bool = False,
        show_unreachable: bool = False,
    ) -> None:
        """
        Display scan results to console.

        Args:
            devices_found: Scan results, devices and failed addresses alike
            show_table: Whether to show device table
            include_beta: Whether beta-only updates count as available
            show_unreachable: Whether to list every address that did not
                answer, not only the ones that failed
        """
        devices, failures = _split_failures(devices_found)

        if show_table:
            self._result_formatter.format_device_table(
                devices, include_beta=include_beta
            )

        if failures:
            self._display_failures(devices, failures, show_unreachable)
        elif devices:
            self._console.print(
                f"\n{Messages.success(f'Found {len(devices)} devices')}"
            )
        else:
            self._console.print(f"\n{Messages.warning('No devices found')}")

    def _display_failures(
        self, devices: list[Any], failures: list[Any], show_unreachable: bool
    ) -> None:
        unanswered = [d for d in failures if d.status == Status.UNREACHABLE]
        errored = [d for d in failures if d.status != Status.UNREACHABLE]
        scanned = len(devices) + len(failures)
        self._console.print(
            "\n"
            + Messages.warning(
                f"Scanned {scanned} addresses: {len(devices)} devices, "
                f"{len(unanswered)} did not answer, {len(errored)} failed"
            )
        )
        for device in errored:
            self._console.print(
                f"  {device.ip}  failed: {escape(device.error_message or 'unknown')}"
            )
        if show_unreachable:
            for device in unanswered:
                reason = escape(device.error_message or "no answer")
                self._console.print(f"  {device.ip}  did not answer: {reason}")
        elif unanswered:
            self._console.print(
                Messages.muted(
                    f"  Run again with --show-unreachable to list the "
                    f"{len(unanswered)} addresses that did not answer."
                )
            )


def _split_failures(results: list[Any]) -> tuple[list[Any], list[Any]]:
    devices = []
    failures = []
    for result in results:
        status = getattr(result, "status", None)
        if status in (Status.UNREACHABLE, Status.ERROR):
            failures.append(result)
        else:
            devices.append(result)
    return devices, failures
