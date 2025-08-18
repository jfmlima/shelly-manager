"""
Device reboot use case for CLI operations.
"""

from typing import Any

from core.domain.value_objects.reboot_device_request import (
    RebootDeviceRequest as CoreRebootDeviceRequest,
)

from rich.console import Console

from cli.dependencies.container import CLIContainer
from cli.entities import DeviceRebootRequest
from cli.presentation.styles import Messages

from ..common.device_discovery import DeviceDiscoveryRequest, DeviceDiscoveryUseCase
from ..common.progress_tracking import ProgressTracker
from ..common.result_formatting import ResultFormatter


class DeviceRebootUseCase:
    """
    Use case for rebooting Shelly devices.

    Handles the CLI orchestration for device rebooting including:
    - Device discovery when using --from-config
    - Confirmation prompts (when not forced)
    - Reboot operations with progress tracking
    - Result formatting and success reporting
    """

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._device_discovery = DeviceDiscoveryUseCase(container)
        self._progress_tracker = ProgressTracker(console)
        self._result_formatter = ResultFormatter(console)

    async def execute(self, request: DeviceRebootRequest) -> list[Any]:
        """
        Execute device reboot operation.

        Args:
            request: Reboot request parameters

        Returns:
            List of reboot results

        Raises:
            ValueError: If no devices are specified
            RuntimeError: If user cancels the operation
        """
        # Validate input
        if not request.devices and not request.from_config:
            raise ValueError("You must specify either device IPs or use --from-config")

        # Get device IPs
        device_ips = await self._get_device_ips(request)

        if not device_ips:
            raise ValueError("No devices found")

        # Confirm action if not forced
        if not request.force:
            if not self._confirm_reboot(len(device_ips)):
                self._console.print(Messages.warning("Reboot cancelled"))
                raise RuntimeError("Reboot cancelled by user")

        # Perform reboots
        return await self._perform_reboots(device_ips)

    async def _get_device_ips(self, request: DeviceRebootRequest) -> list[str]:
        """Get device IPs based on request parameters."""
        if request.from_config and not request.devices:
            self._console.print(
                Messages.config("Getting devices from configuration...")
            )

            discovery_request = DeviceDiscoveryRequest(
                ip_ranges=[],
                devices=[],
                from_config=True,
                timeout=request.timeout,
                workers=request.workers,
            )

            device_list = await self._device_discovery.discover_devices(
                discovery_request
            )
            return [d.ip for d in device_list]
        else:
            return list(request.devices)

    def _confirm_reboot(self, device_count: int) -> bool:
        """Confirm reboot action with user."""
        from cli.commands.common import confirm_action

        return confirm_action(
            f"Are you sure you want to reboot {device_count} device(s)?", default=False
        )

    async def _perform_reboots(self, device_ips: list[str]) -> list[Any]:
        """Perform reboot operations with progress tracking."""
        reboot_interactor = self._container.get_reboot_interactor()
        results = []

        async with self._progress_tracker.track_progress(
            "Rebooting devices...", total=len(device_ips)
        ) as task:
            for device_ip in device_ips:
                try:
                    reboot_request = CoreRebootDeviceRequest(device_ip=device_ip)
                    result = await reboot_interactor.execute(reboot_request)
                    results.append(
                        {
                            "ip": device_ip,
                            "status": "success" if result.success else "failed",
                            "message": result.message,
                        }
                    )
                    self._console.print(
                        Messages.device_success(device_ip, "Reboot initiated")
                    )
                except Exception as e:
                    results.append(
                        {"ip": device_ip, "status": "error", "error": str(e)}
                    )
                    self._console.print(Messages.device_error(device_ip, str(e)))

                task.advance()

        return results

    def display_results(self, results: list[Any]) -> None:
        """Display reboot results to console."""
        successful = len([r for r in results if r["status"] == "success"])
        total = len(results)

        self._console.print(
            f"\n{Messages.success(f'Successfully rebooted {successful}/{total} devices')}"
        )
