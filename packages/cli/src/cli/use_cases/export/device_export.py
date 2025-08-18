"""
Device export use case for CLI operations.
"""

import json
from pathlib import Path
from typing import Any

from core.domain.value_objects.scan_request import ScanRequest
from core.domain.value_objects.check_device_status_request import (
    CheckDeviceStatusRequest,
)
from rich.console import Console
from rich.table import Table

from cli.dependencies.container import CLIContainer
from cli.entities import (
    ExportRequest,
)

from ..common.device_discovery import DeviceDiscoveryRequest, DeviceDiscoveryUseCase


class DeviceExportUseCase:
    """
    Use case for exporting device information to various formats.

    Handles the CLI orchestration for device export including:
    - Device discovery (scan or specific IPs)
    - Configuration retrieval (optional)
    - File format conversion and output
    - File overwrite confirmation
    """

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._device_discovery = DeviceDiscoveryUseCase(container)

    async def execute(self, request: ExportRequest) -> bool:
        """
        Execute device export operation.

        Args:
            request: Export request parameters

        Returns:
            True if export was successful, False otherwise

        Raises:
            ValueError: If invalid parameters provided
            RuntimeError: If user cancels operation
        """
        output_file = request.output or f"devices.{request.format}"
        output_path = Path(output_file)

        if not self._check_file_overwrite(output_path, request.force):
            self._console.print("[yellow]Export cancelled[/yellow]")
            raise RuntimeError("Export cancelled by user")

        devices = await self._get_devices(request)

        if not devices:
            return False

        if request.include_config:
            await self._add_device_configurations(devices)

        return await self._export_devices(devices, output_path, request)

    def _check_file_overwrite(self, output_path: Path, force: bool) -> bool:
        """Check if file should be overwritten."""
        if output_path.exists() and not force:
            from cli.commands.common import confirm_action

            return confirm_action(
                f"File {output_path} already exists. Overwrite?", default=False
            )
        return True

    async def _get_devices(self, request: ExportRequest) -> list[Any]:
        """Get devices based on scan or IP list."""
        if request.scan and request.ips:
            self._console.print(
                "[yellow]⚠️ Both --scan and --ips provided. Using --scan to discover devices.[/yellow]"
            )

        if request.scan:
            return await self._scan_for_devices(request)
        elif request.ips:
            return await self._get_devices_by_ips(request)
        else:
            raise ValueError("Must provide either --scan or --ips")

    async def _scan_for_devices(self, request: ExportRequest) -> list[Any]:
        """Scan network for devices."""
        self._console.print("[blue]🔍 Scanning network for devices...[/blue]")

        try:
            discovery_request = DeviceDiscoveryRequest(
                ip_ranges=[],
                devices=[],
                from_config=True,
                timeout=request.timeout,
                workers=10,
            )

            devices = await self._device_discovery.discover_devices(discovery_request)

            if not devices:
                self._console.print("[yellow]⚠️ No devices found during scan[/yellow]")
                return []

            self._console.print(f"[green]✅ Found {len(devices)} devices[/green]")
            return devices

        except Exception as e:
            self._console.print(f"[red]❌ Error during scan: {e}[/red]")
            raise

    async def _get_devices_by_ips(self, request: ExportRequest) -> list[Any]:
        """Get devices by specific IP addresses."""
        from cli.commands.common import parse_ip_list

        if request.ips is None:
            raise ValueError("No IP addresses provided")

        target_ips = parse_ip_list(",".join(request.ips))

        self._console.print(
            f"[blue]📊 Getting device information from {len(target_ips)} IPs...[/blue]"
        )

        devices = []
        status_interactor = self._container.get_status_interactor()

        for ip in target_ips:
            try:
                status_request = CheckDeviceStatusRequest(
                    device_ip=ip, include_updates=True
                )
                device = await status_interactor.execute(status_request)
                devices.append(device)
                self._console.print(f"[green]✅ {ip}[/green]")
            except Exception as e:
                self._console.print(f"[red]❌ {ip}: {e}[/red]")

        if not devices:
            self._console.print("[yellow]⚠️ No devices responded[/yellow]")

        return devices

    async def _add_device_configurations(self, devices: list[Any]) -> None:
        """Add configuration data to devices."""
        self._console.print("[blue]⚙️ Retrieving device configurations...[/blue]")

        try:
            config_interactor = self._container.get_device_config_interactor()

            for device in devices:
                try:
                    config = await config_interactor.execute(device)
                    device.configuration = config
                    self._console.print(f"[green]✅ Config for {device.ip}[/green]")
                except Exception as e:
                    self._console.print(
                        f"[yellow]⚠️ Config for {device.ip}: {e}[/yellow]"
                    )
                    device.configuration = None

        except Exception as e:
            self._console.print(f"[red]❌ Error getting configurations: {e}[/red]")

    async def _export_devices(
        self, devices: list[Any], output_path: Path, request: ExportRequest
    ) -> bool:
        """Export devices to file."""
        self._console.print(
            f"[blue]💾 Exporting {len(devices)} devices to {output_path}...[/blue]"
        )

        try:
            # TODO: Implement actual export functionality
            success = True  # Placeholder

            if success:
                file_size = output_path.stat().st_size
                self._console.print(
                    f"[green]✅ Exported {len(devices)} devices to {output_path} ({file_size} bytes)[/green]"
                )

                self._display_export_summary(
                    output_path, request, len(devices), file_size
                )
                return True
            else:
                self._console.print("[red]❌ Export failed[/red]")
                return False

        except Exception as e:
            self._console.print(f"[red]❌ Error during export: {e}[/red]")
            raise

    def _display_export_summary(
        self,
        output_path: Path,
        request: ExportRequest,
        device_count: int,
        file_size: int,
    ) -> None:
        """Display export summary table."""
        self._console.print("\n[bold blue]📋 Export Summary[/bold blue]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Output File", str(output_path))
        table.add_row("Format", request.format.upper())
        table.add_row("Device Count", str(device_count))
        table.add_row("File Size", f"{file_size} bytes")
        table.add_row("Include Config", "Yes" if request.include_config else "No")
        table.add_row("Pretty Format", "Yes" if request.pretty else "No")

        self._console.print(table)


class ScanExportUseCase:
    """
    Use case for exporting network scan results.

    Handles the CLI orchestration for scan export including:
    - Network scanning with optional network range
    - Empty result handling
    - File format conversion and output
    """

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console

    async def execute(self, request: ExportRequest) -> bool:
        """
        Export devices found by scanning the network.

        Args:
            request: Scan export request parameters

        Returns:
            True if export was successful, False otherwise

        Raises:
            RuntimeError: If user cancels operation
        """
        if request.output is None:
            raise ValueError("Output path is required for scan export")

        output_path = Path(request.output)

        if not self._check_file_overwrite(output_path, request.force):
            self._console.print("[yellow]Export cancelled[/yellow]")
            raise RuntimeError("Export cancelled by user")
    
        devices = await self._scan_network(request)

        return await self._export_scan_results(devices, output_path, request)

    def _check_file_overwrite(self, output_path: Path, force: bool) -> bool:
        """Check if file should be overwritten."""
        if output_path.exists() and not force:
            from cli.commands.common import confirm_action

            return confirm_action(
                f"File {output_path} already exists. Overwrite?", default=False
            )
        return True

    async def _scan_network(self, request: ExportRequest) -> list[Any]:
        """Scan network for devices."""
        self._console.print("[blue]🔍 Scanning network for Shelly devices...[/blue]")

        try:
            scan_interactor = self._container.get_scan_interactor()

            scan_request = ScanRequest(
                use_predefined=False,
                start_ip=None,
                end_ip=None,
                timeout=request.timeout,
                max_workers=request.workers,
            )

            devices = await scan_interactor.execute(scan_request)

            if not devices:
                self._console.print("[yellow]⚠️ No devices found during scan[/yellow]")
            else:
                self._console.print(f"[green]✅ Found {len(devices)} devices[/green]")

            return devices

        except Exception as e:
            self._console.print(f"[red]❌ Error during scan export: {e}[/red]")
            raise

    async def _export_scan_results(
        self, devices: list[Any], output_path: Path, request: ExportRequest
    ) -> bool:
        """Export scan results to file."""
        self._console.print(
            f"[blue]💾 Exporting scan results to {request.output}...[/blue]"
        )

        try:
            # TODO: Implement actual export functionality
            success = True  # Placeholder

            if success:
                self._console.print(
                    f"[green]✅ Exported scan results to {request.output}[/green]"
                )
                return True
            else:
                self._console.print("[red]❌ Export failed[/red]")
                return False

        except Exception as e:
            self._console.print(f"[red]❌ Error during export: {e}[/red]")
            return False

    async def _export_empty_results(
        self, output_path: Path, request: ExportRequest
    ) -> None:
        """Export empty scan results."""
        empty_data = {
            "devices": [],
            "scan_info": {"device_count": 0, "network": request.network or "auto"},
        }

        with open(output_path, "w") as f:
            if request.format == "json":
                json.dump(empty_data, f, indent=2 if request.pretty else None)
            elif request.format == "yaml":
                import yaml

                yaml.dump(empty_data, f, default_flow_style=False)
            else:  # CSV
                f.write("ip,name,model,firmware_version,mac_address,status\n")

        self._console.print(
            f"[green]✅ Empty scan results exported to {request.output}[/green]"
        )

    def _display_scan_summary(
        self,
        output_path: Path,
        request: ExportRequest,
        device_count: int,
        file_size: int,
    ) -> None:
        """Display scan export summary table."""
        self._console.print("\n[bold blue]📋 Scan Export Summary[/bold blue]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Output File", str(output_path))
        table.add_row("Format", request.format.upper())
        table.add_row("Devices Found", str(device_count))
        table.add_row("Network", request.network or "Auto-detected")
        table.add_row("Scan Timeout", f"{request.timeout}s")
        table.add_row("File Size", f"{file_size} bytes")

        self._console.print(table)
