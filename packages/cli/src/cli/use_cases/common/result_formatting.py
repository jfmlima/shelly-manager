"""
Result formatting utilities for CLI operations.
"""

from typing import Any

from rich.console import Console
from rich.table import Table

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
