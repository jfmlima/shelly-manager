"""
Export-related Click commands.
"""

import click

from ..entities import ExportRequest
from ..use_cases.export.device_export import DeviceExportUseCase
from .common import (
    async_command,
    device_targeting_options,
)


@click.group()
def export_commands() -> None:
    pass


@export_commands.command()
@click.argument("targets", nargs=-1)
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
@device_targeting_options
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
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    timeout: float,
    include_config: bool,
    pretty: bool,
    force: bool,
) -> None:
    """
    📤 Export device information and configurations.

    Export device data to JSON, CSV, or YAML format. Supports IP addresses, ranges,
    and CIDR notation via the targeting system.

    Examples:
      shelly-manager export devices --scan
      shelly-manager export devices 192.168.1.0/24 --format csv
      shelly-manager export devices -t 192.168.1.100 -t 192.168.1.101 --include-config -o my-devices.json
    """
    console = ctx.obj.console
    container = ctx.obj.container

    export_use_case = DeviceExportUseCase(container, console)

    request = ExportRequest(
        output=output,
        format=format,
        scan=scan,
        targets=list(targets) + list(targets_opt),
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
