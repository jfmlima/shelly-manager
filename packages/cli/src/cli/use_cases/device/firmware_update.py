"""
Firmware update use case for CLI operations.
"""

from typing import Any

from core.domain.enums.enums import UpdateChannel
from rich.console import Console

from cli.dependencies.container import CLIContainer
from cli.entities import FirmwareUpdateRequest
from cli.presentation.styles import Icons, Messages

from ..common.device_discovery import DeviceDiscoveryRequest, DeviceDiscoveryUseCase
from ..common.progress_tracking import ProgressTracker
from ..common.result_formatting import ResultFormatter


class FirmwareUpdateUseCase:
    """
    Use case for updating Shelly device firmware.

    Handles the CLI orchestration for firmware updates including:
    - Device discovery when using --from-config
    - Update checking and availability detection
    - Firmware update operations with progress tracking
    - Result formatting and success reporting
    """

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._device_discovery = DeviceDiscoveryUseCase(container)
        self._progress_tracker = ProgressTracker(console)
        self._result_formatter = ResultFormatter(console)

    def _convert_channel_to_enum(self, channel: str) -> Any:
        """Convert string channel to core UpdateChannel enum."""
        try:
            # Try to import the enum from core
            return (
                UpdateChannel.STABLE
                if channel.lower() == "stable"
                else UpdateChannel.BETA
            )
        except ImportError:
            # If import fails, create a mock object with the right interface
            class MockChannel:
                def __init__(self, value: str):
                    self.value = value

            return MockChannel("stable" if channel.lower() == "stable" else "beta")

    async def execute(self, request: FirmwareUpdateRequest) -> list[Any]:
        """
        Execute firmware update operation.

        Args:
            request: Firmware update request parameters

        Returns:
            List of update results

        Raises:
            ValueError: If no devices are specified
            RuntimeError: If user cancels the operation
        """
        # Validate input
        if not request.devices and not request.from_config:
            raise ValueError("No devices specified")

        # Get device list
        device_ips = await self._get_device_list(request)
        if not device_ips:
            raise ValueError("No devices found")

        self._console.print(
            Messages.process(
                f"Checking firmware updates for {len(device_ips)} device(s) on {request.channel} channel",
                Icons.SIGNAL,
            )
        )

        # Check for updates
        devices_with_updates = await self._check_for_updates(
            device_ips, request.channel
        )

        if not devices_with_updates:
            self._console.print(
                f"\n{Messages.success('All devices are up to date!', Icons.CELEBRATION)}"
            )
            return []

        self._console.print(
            f"\n{Messages.warning(f'{len(devices_with_updates)} device(s) have updates available', Icons.PACKAGE)}"
        )

        for device in devices_with_updates:
            self._console.print(
                f"  {device['ip']}: {device['current_version']} → {device['new_version']}"
            )

        if request.check_only:
            self._console.print(
                f"\n{Messages.info('Check-only mode: No updates were installed')}"
            )
            return devices_with_updates

        # Confirm update if not forced
        if not request.force:
            from cli.commands.common import confirm_action

            if not confirm_action(
                f"Proceed with updating {len(devices_with_updates)} device(s)?",
                default=False,
            ):
                self._console.print(Messages.warning("Update cancelled"))
                raise RuntimeError("Update cancelled by user")

        # Perform updates
        return await self._perform_updates(devices_with_updates, request.channel)

    async def _get_device_list(self, request: FirmwareUpdateRequest) -> list[str]:
        """Get list of device IPs based on request parameters."""
        if request.from_config:
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

    async def _check_for_updates(
        self, device_ips: list[str], channel: str
    ) -> list[dict[str, Any]]:
        """Check which devices have firmware updates available."""
        update_interactor = self._container.get_update_interactor()
        devices_with_updates = []

        # Convert channel string to enum
        channel_enum = self._convert_channel_to_enum(channel)

        async with self._progress_tracker.track_progress(
            "Checking for updates...", total=len(device_ips)
        ) as progress_task:

            for device_ip in device_ips:
                try:
                    result = await update_interactor.execute(device_ip, channel_enum)
                    if result.success:
                        # Parse update information from result
                        update_info = result.data if hasattr(result, "data") else {}
                        if isinstance(update_info, dict) and update_info.get(
                            "update_available"
                        ):
                            devices_with_updates.append(
                                {
                                    "ip": device_ip,
                                    "current_version": update_info.get(
                                        "current_version", "Unknown"
                                    ),
                                    "new_version": update_info.get(
                                        "new_version", "Unknown"
                                    ),
                                    "update_available": True,
                                }
                            )
                            self._console.print(
                                Messages.device_action(
                                    device_ip, "Update available", Icons.PACKAGE
                                )
                            )
                        else:
                            self._console.print(
                                Messages.device_success(device_ip, "Up to date")
                            )
                    else:
                        self._console.print(
                            Messages.device_success(device_ip, "Up to date")
                        )
                except Exception as e:
                    self._console.print(
                        Messages.device_error(
                            device_ip, f"Error checking updates - {e}"
                        )
                    )

                progress_task.advance()

        return devices_with_updates

    async def _perform_updates(
        self, devices_with_updates: list[dict[str, Any]], channel: str
    ) -> list[Any]:
        """Perform firmware updates on devices."""
        self._console.print(
            f"\n{Messages.process('Starting firmware updates...', Icons.ROCKET)}"
        )

        update_interactor = self._container.get_update_interactor()
        successful_updates = 0
        results = []

        # Convert channel string to enum
        channel_enum = self._convert_channel_to_enum(channel)

        async with self._progress_tracker.track_progress(
            "Updating devices...", total=len(devices_with_updates)
        ) as progress_task:

            for device in devices_with_updates:
                device_ip = device["ip"]
                try:
                    self._console.print(
                        Messages.device_action(device_ip, "Updating...", Icons.UPDATE)
                    )
                    result = await update_interactor.execute(device_ip, channel_enum)

                    if result.success:
                        self._console.print(
                            Messages.device_success(
                                device_ip, "Update completed successfully"
                            )
                        )
                        successful_updates += 1
                        results.append(
                            {
                                "ip": device_ip,
                                "success": True,
                                "message": "Update completed successfully",
                            }
                        )
                    else:
                        error_msg = (
                            str(result.message)
                            if hasattr(result, "message")
                            else "Update failed"
                        )
                        self._console.print(
                            Messages.device_error(
                                device_ip, f"Update failed - {error_msg}"
                            )
                        )
                        results.append(
                            {"ip": device_ip, "success": False, "message": error_msg}
                        )

                except Exception as e:
                    self._console.print(
                        Messages.device_error(device_ip, f"Update error - {e}")
                    )
                    results.append(
                        {"ip": device_ip, "success": False, "message": str(e)}
                    )

                progress_task.advance()

        self._console.print(
            f"\n{Messages.success(f'Successfully updated {successful_updates}/{len(devices_with_updates)} devices', Icons.CELEBRATION)}"
        )

        if successful_updates < len(devices_with_updates):
            self._console.print(
                Messages.warning(
                    "Some devices failed to update. Check logs for details."
                )
            )

        return results


__all__ = ["FirmwareUpdateUseCase"]
