"""
Result formatting utilities for CLI operations.
"""

from typing import Any

from core.domain.entities import DeviceStatus, DiscoveredDevice
from rich.console import Console
from rich.table import Table

from cli.entities.bulk import BulkOperationResult
from cli.presentation.styles import format_device_status


class ResultFormatter:
    """
    Utility for formatting and displaying operation results.
    """

    def __init__(self, console: Console):
        self._console = console

    def format_device_table(
        self, devices: list[Any], title: str = "Shelly Devices"
    ) -> None:
        """
        Format and display a table of devices.

        Args:
            devices: List of device objects or dictionaries
            title: Table title
        """
        if not devices:
            return

        if devices and isinstance(devices[0], DiscoveredDevice):
            self._format_discovered_devices_table(devices, title)
        elif devices and isinstance(devices[0], DeviceStatus):
            self._format_device_status_table(devices)
        else:
            self._format_legacy_device_table(devices, title)

    def _format_discovered_devices_table(
        self, devices: list[DiscoveredDevice], title: str
    ) -> None:
        """Format table for DiscoveredDevice entities."""
        table = Table(title=title)
        table.add_column("IP Address", style="cyan")
        table.add_column("Device Type", style="green")
        table.add_column("Name", style="blue")
        table.add_column("Firmware", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Response Time", style="dim")

        for device in devices:
            response_time = (
                f"{device.response_time:.2f}s" if device.response_time else "N/A"
            )
            table.add_row(
                device.ip,
                device.device_type or "Unknown",
                device.device_name or "Unknown",
                device.firmware_version or "Unknown",
                format_device_status(device.status),
                response_time,
            )

        self._console.print(table)

    def _format_device_status_table(self, devices: list[DeviceStatus]) -> None:
        """Format table for DeviceStatus entities."""

        for device_status in devices:
            self.format_detailed_device_status(device_status)

    def _format_legacy_device_table(self, devices: list[Any], title: str) -> None:
        """Legacy format for backward compatibility."""
        table = Table(title=title)
        table.add_column("IP Address", style="cyan")
        table.add_column("Device Type", style="green")
        table.add_column("Name", style="blue")
        table.add_column("Firmware", style="magenta")
        table.add_column("Status", style="yellow")

        for device in devices:
            if hasattr(device, "ip"):
                ip = device.ip
                device_type = getattr(device, "device_type", "Unknown")
                name = getattr(device, "device_name", "Unknown")
                firmware = getattr(device, "firmware_version", "Unknown")
                status = getattr(device, "status", "Unknown")
            else:
                ip = device.get("ip", "Unknown")
                device_type = device.get("device_type", "Unknown")
                name = device.get("device_name", "Unknown")
                firmware = device.get("firmware_version", "Unknown")
                status = device.get("status", "Unknown")

            table.add_row(ip, device_type, name, firmware, format_device_status(status))

        self._console.print(table)

    def format_detailed_device_status(self, device_status: DeviceStatus) -> None:
        """Format detailed component information for a single device."""
        from rich.columns import Columns
        from rich.panel import Panel

        # Device header
        system_info = device_status.get_system_info()
        device_name = system_info.device_name if system_info else "Unknown Device"

        header = f"[bold cyan]{device_name}[/bold cyan] ([yellow]{device_status.device_ip}[/yellow])"
        self._console.print(f"\n{header}")

        # System information panel
        if system_info:
            system_content = []
            system_content.append(
                f"[green]Firmware:[/green] {system_info.firmware_version}"
            )
            system_content.append(f"[green]MAC:[/green] {system_info.mac_address}")
            system_content.append(
                f"[green]Restart Required:[/green] {'Yes' if system_info.restart_required else 'No'}"
            )

            # Show available firmware updates with version information
            if system_info.available_updates:
                device_summary = device_status.get_device_summary()
                available_updates = device_summary.get("available_updates", {})

                if available_updates:
                    system_content.append("[yellow]Updates Available:[/yellow]")
                    for update_type, update_info in available_updates.items():
                        version = update_info.get("version", "Unknown")
                        name = update_info.get("name", update_type) or update_type
                        system_content.append(f"  [cyan]• {name}:[/cyan] {version}")
                else:
                    system_content.append(
                        f"[yellow]Updates Available:[/yellow] {len(system_info.available_updates)}"
                    )

            system_panel = Panel(
                "\n".join(system_content),
                title="[bold]System Info[/bold]",
                border_style="green",
            )
        else:
            system_panel = Panel(
                "[red]No system information available[/red]",
                title="[bold]System Info[/bold]",
                border_style="red",
            )

        # Component panels
        panels = [system_panel]

        # Switches
        switches = device_status.get_switches()
        if switches:
            switch_content = []
            for switch in switches:
                state = "ON" if switch.output else "OFF"
                switch_content.append(f"[green]{switch.name}:[/green] {state}")
            panels.append(
                Panel(
                    "\n".join(switch_content),
                    title="[bold]Switches[/bold]",
                    border_style="blue",
                )
            )

        # Inputs
        inputs = device_status.get_inputs()
        if inputs:
            input_content = []
            for inp in inputs:
                state = "ACTIVE" if inp.state else "INACTIVE"
                input_content.append(f"[green]{inp.name}:[/green] {state}")
            panels.append(
                Panel(
                    "\n".join(input_content),
                    title="[bold]Inputs[/bold]",
                    border_style="cyan",
                )
            )

        # Covers
        covers = device_status.get_covers()
        if covers:
            cover_content = []
            for cover in covers:
                position = (
                    f"{cover.position}%" if cover.position is not None else "Unknown"
                )
                cover_content.append(
                    f"[green]{cover.name}:[/green] {cover.state} ({position})"
                )
            panels.append(
                Panel(
                    "\n".join(cover_content),
                    title="[bold]Covers[/bold]",
                    border_style="magenta",
                )
            )

        # Display panels in columns
        if len(panels) > 1:
            self._console.print(Columns(panels, equal=True))
        else:
            self._console.print(panels[0])

    def format_operation_results(
        self, results: list[dict], operation_name: str
    ) -> None:
        """
        Format and display results from device operations.

        Args:
            results: List of operation results
            operation_name: Name of the operation performed
        """
        successful = len([r for r in results if r.get("status") == "success"])
        total = len(results)

        if successful == total:
            from cli.presentation.styles import Messages

            self._console.print(
                f"\n{Messages.success(f'Successfully {operation_name.lower()} {successful}/{total} devices')}"
            )
        else:
            from cli.presentation.styles import Messages

            self._console.print(
                f"\n{Messages.warning(f'{operation_name} completed: {successful}/{total} successful')}"
            )

    def display_bulk_operation_result(self, result: BulkOperationResult) -> None:
        """Display bulk operation results in a formatted table."""
        from rich.table import Table

        table = Table(
            title=f"Bulk {result.operation_type.replace('_', ' ').title()} Results"
        )
        table.add_column("Device IP", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Message", style="dim")

        for device_ip, device_result in result.device_results.items():
            status = (
                "[green]✓ Success[/green]"
                if device_result.status == "success"
                else "[red]✗ Failed[/red]"
            )
            message = device_result.message or device_result.error or "No details"
            table.add_row(device_ip, status, message)

        self._console.print(table)
        self._console.print()

        if result.time_taken_seconds:
            self._console.print(
                f"[dim]Time taken: {result.time_taken_seconds:.2f} seconds[/dim]"
            )

        self._console.print(
            f"[bold blue]Summary:[/bold blue] {result.successful_operations}/{result.total_devices} operations successful"
        )

        if result.failed_operations > 0:
            self._console.print(
                f"[yellow]{result.failed_operations} operations failed[/yellow]"
            )

            if result.errors_by_device:
                self._console.print("\n[bold red]Error Details:[/bold red]")
                for device_ip, error in result.errors_by_device.items():
                    self._console.print(f"  [red]{device_ip}:[/red] {error}")

        if result.status == "success":
            self._console.print(
                f"[green]✓ Bulk {result.operation_type.replace('_', ' ')} completed successfully[/green]"
            )
        else:
            self._console.print(
                f"[red]✗ Bulk {result.operation_type.replace('_', ' ')} failed[/red]"
            )
