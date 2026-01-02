"""
Device export use case for CLI operations.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.domain.entities import DeviceStatus
from core.domain.value_objects.check_device_status_request import (
    CheckDeviceStatusRequest,
)
from core.utils.target_parser import expand_targets
from rich.console import Console
from rich.table import Table

from cli.dependencies.container import CLIContainer
from cli.entities import (
    ExportRequest,
)


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

        return await self._export_devices(devices, output_path, request)

    def _check_file_overwrite(self, output_path: Path, force: bool) -> bool:
        """Check if file should be overwritten."""
        if output_path.exists() and not force:
            from cli.commands.common import confirm_action

            return confirm_action(
                f"File {output_path} already exists. Overwrite?", default=False
            )
        return True

    async def _get_all_target_ips(self, request: ExportRequest) -> list[str]:
        """Get all target IPs from request targets."""
        if not request.targets:
            return []

        try:
            return expand_targets(request.targets)
        except ValueError as e:
            self._console.print(f"[red]❌ Error parsing targets: {e}[/red]")
            return []

    async def _get_detailed_status_for_devices(
        self, device_ips: list[str]
    ) -> list[DeviceStatus]:
        """Get detailed DeviceStatus for a list of IPs. Excludes failed devices."""
        devices: list[DeviceStatus] = []
        status_interactor = self._container.get_status_interactor()

        self._console.print(
            f"[blue]📊 Getting status from {len(device_ips)} devices...[/blue]"
        )

        for ip in device_ips:
            try:
                status_request = CheckDeviceStatusRequest(
                    device_ip=ip, include_updates=True
                )
                device = await status_interactor.execute(status_request)
                if device is not None:
                    devices.append(device)
                    self._console.print(f"[green]✅ {ip}[/green]")
                else:
                    self._console.print(f"[yellow]⚠️ {ip}: No response[/yellow]")
            except Exception as e:
                self._console.print(f"[red]❌ {ip}: {e}[/red]")

        if not devices:
            self._console.print("[yellow]⚠️ No devices responded[/yellow]")

        return devices

    async def _get_devices(self, request: ExportRequest) -> list[DeviceStatus]:
        """Get devices based on targets."""
        if not request.targets:
            raise ValueError(
                "No targets specified. Provide device IPs, ranges, or CIDR."
            )

        target_ips = await self._get_all_target_ips(request)

        if not target_ips:
            return []

        return await self._get_detailed_status_for_devices(target_ips)

    # _scan_for_devices and _get_devices_by_ips merged into _get_devices and _get_all_target_ips

    async def _get_configurations_for_devices(
        self, devices: list[DeviceStatus]
    ) -> dict[str, dict[str, Any]]:
        """Get configuration data for devices, returning a mapping of device_ip -> config."""
        self._console.print("[blue]⚙️ Retrieving device configurations...[/blue]")

        try:
            bulk_operations = self._container.get_bulk_operations_interactor()
            device_ips = [device.device_ip for device in devices]

            component_types = [
                "switch",
                "input",
                "cover",
                "sys",
                "cloud",
                "ble",
                "zigbee",
            ]
            bulk_config_result = await bulk_operations.export_bulk_config(
                device_ips, component_types
            )

            devices_data = bulk_config_result.get("devices", {})

            result = {}
            for device_ip in device_ips:
                if device_ip in devices_data:

                    device_data = devices_data[device_ip]
                    result[device_ip] = device_data.get("components", {})
                    self._console.print(f"[green]✅ Config for {device_ip}[/green]")
                else:
                    self._console.print(
                        f"[yellow]⚠️ Config for {device_ip}: Device not found in bulk export[/yellow]"
                    )

            return result

        except Exception as e:
            self._console.print(f"[red]❌ Error getting configurations: {e}[/red]")
            return {}

    async def _export_devices(
        self, devices: list[DeviceStatus], output_path: Path, request: ExportRequest
    ) -> bool:
        """Export devices to file."""
        self._console.print(
            f"[blue]💾 Exporting {len(devices)} devices to {output_path}...[/blue]"
        )

        try:

            config_data = {}
            if request.include_config:
                config_data = await self._get_configurations_for_devices(devices)

            export_data = self._prepare_export_data(devices, request, config_data)

            if request.format.lower() == "json":
                self._write_json_export(export_data, output_path, request.pretty)
            elif request.format.lower() == "yaml":
                self._write_yaml_export(export_data, output_path)
            elif request.format.lower() == "csv":
                self._write_csv_export(export_data["devices"], output_path)
            else:
                raise ValueError(f"Unsupported export format: {request.format}")

            file_size = output_path.stat().st_size
            self._console.print(
                f"[green]✅ Exported {len(devices)} devices to {output_path} ({file_size} bytes)[/green]"
            )

            self._display_export_summary(output_path, request, len(devices), file_size)
            return True

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

    def _prepare_export_data(
        self,
        devices: list[DeviceStatus],
        request: ExportRequest,
        config_data: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Prepare devices data for export."""
        export_data: dict[str, Any] = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "export_type": "device_export",
                "format": request.format,
                "include_config": request.include_config,
                "total_devices": len(devices),
            },
            "devices": [],
        }

        if request.targets:
            export_data["metadata"]["scan_settings"] = {
                "targets": request.targets,
                "timeout": request.timeout,
            }

        for device in devices:
            device_config = config_data.get(device.device_ip) if config_data else None
            device_data = self._device_to_dict(device, device_config)
            export_data["devices"].append(device_data)

        return export_data

    def _device_to_dict(
        self, device: DeviceStatus, device_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Convert DeviceStatus object to dictionary."""

        device_dict: dict[str, Any] = {
            "ip": device.device_ip,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "firmware_version": device.firmware_version,
            "mac_address": device.mac_address,
            "last_updated": (
                device.last_updated.isoformat() if device.last_updated else None
            ),
        }

        summary = device.get_device_summary()
        device_dict["summary"] = {
            "switch_count": summary["switch_count"],
            "input_count": summary["input_count"],
            "cover_count": summary["cover_count"],
            "total_power": summary["total_power"],
            "any_switch_on": summary["any_switch_on"],
            "cloud_connected": summary["cloud_connected"],
            "has_updates": summary["has_updates"],
            "restart_required": summary["restart_required"],
        }

        if device_config:
            device_dict["configuration"] = device_config

        return device_dict

    def _write_json_export(
        self, data: dict[str, Any], output_path: Path, pretty: bool = False
    ) -> None:
        """Write export data as JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)

    def _write_yaml_export(self, data: dict[str, Any], output_path: Path) -> None:
        """Write export data as YAML."""
        try:
            import yaml
        except ImportError as e:
            raise ImportError(
                "PyYAML is required for YAML export. Install with: pip install pyyaml"
            ) from e

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def _write_csv_export(
        self, device_data: list[dict[str, Any]], output_path: Path
    ) -> None:
        """Write prepared device data as CSV (tabular summary)."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "ip",
                "device_name",
                "device_type",
                "firmware_version",
                "mac_address",
                "status",
                "last_updated",
                "switch_count",
                "input_count",
                "cover_count",
                "total_power",
                "cloud_connected",
                "has_updates",
                "restart_required",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for device_dict in device_data:

                csv_device = device_dict.copy()

                if "summary" in csv_device:
                    summary = csv_device.pop("summary")
                    csv_device.update(summary)

                csv_row = {field: csv_device.get(field, "") for field in fieldnames}
                writer.writerow(csv_row)
