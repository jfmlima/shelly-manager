"""
Export-related Click commands.
"""

import click

from ..entities import ExportRequest
from ..use_cases.export.device_export import DeviceExportUseCase
from .common import async_command


@click.group()
def export_commands() -> None:
    pass


@export_commands.command()
@click.option(
    "--output", "-o", type=click.Path(), help="Output file path (default: devices.json)"
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "yaml"], case_sensitive=False),
    default="json",
    help="Export format (default: json)",
)
@click.option("--scan", is_flag=True, help="Scan network for devices before export")
@click.option("--ips", help="Comma-separated list of IP addresses to export")
@click.option("--network", help="Network range to scan (e.g., 192.168.1.0/24)")
@click.option(
    "--timeout",
    type=float,
    default=5.0,
    help="Request timeout in seconds (default: 5.0)",
)
@click.option(
    "--include-config", is_flag=True, help="Include device configuration in export"
)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output")
@click.option("--force", is_flag=True, help="Overwrite existing output file")
@click.pass_context
@async_command
async def devices(
    ctx: click.Context,
    output: str,
    format: str,
    scan: bool,
    ips: str,
    network: str,
    timeout: int,
    include_config: bool,
    pretty: bool,
    force: bool,
) -> None:
    """
    📤 Export device information and configurations.

    Export device data to JSON, CSV, or YAML format. Supports scanning
    for devices or using a predefined list of IP addresses.

    Examples:
      shelly-manager export devices --scan
      shelly-manager export devices --ips 192.168.1.100,192.168.1.101 --format csv
      shelly-manager export devices --scan --include-config --output my-devices.json
      shelly-manager export devices --scan --network 192.168.1.0/24 --format yaml
    """
    console = ctx.obj.console
    container = ctx.obj.container

    export_use_case = DeviceExportUseCase(container, console)

    request = ExportRequest(
        output=output,
        format=format,
        scan=scan,
        ips=ips.split(",") if ips else None,
        network=network,
        timeout=timeout,
        include_config=include_config,
        pretty=pretty,
        force=force,
    )

    try:
        success = await export_use_case.execute(request)
        if not success:
            raise click.Abort()
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise click.Abort() from None
    except RuntimeError:
        return


__all__ = ["export_commands"]
