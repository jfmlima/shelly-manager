"""
Configuration update use case for CLI operations.
"""

import json
from typing import Any

from core.domain.value_objects.set_configuration_request import SetConfigurationRequest

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from cli.dependencies.container import CLIContainer
from cli.entities import DeviceConfigUpdateRequest
from cli.presentation.styles import Icons, Messages

from ..common.device_discovery import DeviceDiscoveryRequest, DeviceDiscoveryUseCase
from ..common.progress_tracking import ProgressTracker
from ..common.result_formatting import ResultFormatter


class ConfigUpdateUseCase:
    """
    Use case for updating Shelly device configuration.

    Handles the CLI orchestration for configuration updates including:
    - Device discovery when using --from-config
    - Configuration file loading and validation
    - Configuration update operations with progress tracking
    - Result formatting and success reporting
    """

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._device_discovery = DeviceDiscoveryUseCase(container)
        self._progress_tracker = ProgressTracker(console)
        self._result_formatter = ResultFormatter(console)

    async def execute(self, request: DeviceConfigUpdateRequest) -> list[Any]:
        """
        Execute configuration update operation.

        Args:
            request: Configuration update request parameters

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
                f"Updating configuration for {len(device_ips)} device(s)", Icons.SIGNAL
            )
        )

        # Load config data from file if provided
        config_data = {}
        if request.config_file:
            self._console.print(
                Messages.muted(f"Using configuration file: {request.config_file}")
            )
            config_data = await self._load_config_file(request.config_file)

        # Confirm update if not forced
        if not request.force:
            from cli.commands.common import confirm_action

            if not confirm_action(
                f"Apply configuration updates to {len(device_ips)} device(s)?",
                default=False,
            ):
                self._console.print(Messages.warning("Configuration update cancelled"))
                raise RuntimeError("Configuration update cancelled by user")

        # Perform configuration updates
        return await self._perform_config_updates(device_ips, config_data)

    async def _get_device_list(self, request: DeviceConfigUpdateRequest) -> list[str]:
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

    async def _load_config_file(self, config_file: str) -> dict[str, Any]:
        """Load configuration data from file."""
        try:
            with open(config_file) as f:
                config_data = json.load(f)
            if not isinstance(config_data, dict):
                raise ValueError("Config file must contain a JSON object")
            return config_data
        except Exception as e:
            self._console.print(Messages.error(f"Failed to load config file: {e}"))
            raise ValueError(f"Failed to load config file: {e}") from e

    async def _perform_config_updates(
        self, device_ips: list[str], config_data: dict[str, Any]
    ) -> list[Any]:
        """Perform configuration updates on devices."""
        set_config_interactor = self._container.get_device_config_set_interactor()
        successful_updates = 0
        results: list[Any] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self._console,
            transient=False,
        ) as progress:
            update_task = progress.add_task(
                "Updating configurations...", total=len(device_ips)
            )

            for device_ip in device_ips:
                try:
                    self._console.print(
                        f"[blue]⚙️ Updating configuration for {device_ip}...[/blue]"
                    )
                    config_request = SetConfigurationRequest(
                        device_ip=device_ip, config=config_data
                    )
                    result = await set_config_interactor.execute(config_request)
                    if result.get("success"):
                        self._console.print(
                            f"[green]✅ {device_ip}: Configuration updated successfully[/green]"
                        )
                        successful_updates += 1
                        results.append(
                            {
                                "ip": device_ip,
                                "success": True,
                                "message": "Configuration updated successfully",
                            }
                        )
                    else:
                        error_msg = result.get("message", "Unknown error")
                        self._console.print(
                            f"[red]❌ {device_ip}: Configuration update failed - {error_msg}[/red]"
                        )
                        results.append(
                            {"ip": device_ip, "success": False, "message": error_msg}
                        )
                except Exception as e:
                    self._console.print(
                        f"[red]❌ {device_ip}: Configuration update error - {e}[/red]"
                    )
                    results.append(
                        {"ip": device_ip, "success": False, "message": str(e)}
                    )
                progress.advance(update_task)

        self._console.print(
            f"\n[green]🎉 Successfully updated configuration on {successful_updates}/{len(device_ips)} devices[/green]"
        )
        if successful_updates < len(device_ips):
            self._console.print(
                "[yellow]⚠️ Some devices failed to update. Check logs for details.[/yellow]"
            )
        return results


__all__ = ["ConfigUpdateUseCase"]
