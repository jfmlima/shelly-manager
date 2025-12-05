"""
Bulk operations commands for the CLI.
"""

import asyncio
import json
from pathlib import Path

import click

from cli.commands.common import device_targeting_options
from cli.entities.bulk import (
    BulkConfigApplyRequest,
    BulkConfigExportRequest,
    BulkOperationRequest,
    BulkRebootRequest,
)
from cli.use_cases.device.bulk_operations import BulkOperationsUseCase


@click.group()
def bulk() -> None:
    """
    🔄 Bulk operations on multiple devices.

    Perform actions on multiple Shelly devices simultaneously.
    Supports device discovery, configuration-based selection,
    or specific IP addresses.
    """
    pass


@bulk.command()
@device_targeting_options
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.option(
    "--workers",
    type=int,
    default=10,
    help="Number of concurrent operations (default: 10)",
)
@click.pass_context
def reboot(
    ctx: click.Context,
    from_config: bool,
    devices: tuple[str, ...],
    force: bool,
    workers: int,
) -> None:
    """
    🔄 Reboot multiple devices.

    Examples:
      shelly-manager bulk reboot --from-config
      shelly-manager bulk reboot --devices 192.168.1.100 192.168.1.101
    """
    console = ctx.obj.console
    container = ctx.obj.container

    bulk_use_case = BulkOperationsUseCase(container, console)

    request = BulkRebootRequest(
        devices=list(devices),
        from_config=from_config,
        force=force,
        workers=workers,
    )

    result = asyncio.run(bulk_use_case.execute_bulk_reboot(request))
    bulk_use_case.display_bulk_results(result)


@bulk.command()
@device_targeting_options
@click.option(
    "--channel",
    type=click.Choice(["stable", "beta"]),
    default="stable",
    help="Update channel (default: stable)",
)
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.option(
    "--workers",
    type=int,
    default=10,
    help="Number of concurrent operations (default: 10)",
)
@click.pass_context
def update(
    ctx: click.Context,
    from_config: bool,
    devices: tuple[str, ...],
    channel: str,
    force: bool,
    workers: int,
) -> None:
    """
    📦 Update firmware on multiple devices.

    Examples:
      shelly-manager bulk update --from-config --channel stable
      shelly-manager bulk update --devices 192.168.1.100 192.168.1.101 --channel beta
    """
    console = ctx.obj.console
    container = ctx.obj.container

    bulk_use_case = BulkOperationsUseCase(container, console)

    request = BulkOperationRequest(
        devices=list(devices),
        from_config=from_config,
        force=force,
        workers=workers,
    )

    result = asyncio.run(bulk_use_case.execute_bulk_update(request, channel))
    bulk_use_case.display_bulk_results(result)


@bulk.group()
def config() -> None:
    """
    ⚙️ Bulk configuration operations.

    Export and apply component configurations across multiple devices.
    """
    pass


@config.command()
@device_targeting_options
@click.option(
    "--components",
    required=True,
    help="Comma-separated list of component types (e.g., switch,input,cover)",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(),
    help="Output file path for exported configuration",
)
@click.option("--force", is_flag=True, help="Overwrite output file if it exists")
@click.option(
    "--workers",
    type=int,
    default=10,
    help="Number of concurrent operations (default: 10)",
)
@click.pass_context
def export(
    ctx: click.Context,
    from_config: bool,
    devices: tuple[str, ...],
    components: str,
    output: str,
    force: bool,
    workers: int,
) -> None:
    """
    📤 Export component configurations from multiple devices.

    Examples:
      shelly-manager bulk config export --from-config --components switch,input --output configs.json
      shelly-manager bulk config export --devices 192.168.1.100,192.168.1.101 --components switch --output switch-configs.json
    """
    console = ctx.obj.console
    container = ctx.obj.container

    component_types = [comp.strip() for comp in components.split(",")]

    output_path = Path(output)
    if output_path.exists() and not force:
        console.print(
            f"[red]Error: Output file '{output}' already exists. Use --force to overwrite."
        )
        raise click.Abort()

    bulk_use_case = BulkOperationsUseCase(container, console)

    request = BulkConfigExportRequest(
        devices=list(devices),
        from_config=from_config,
        component_types=component_types,
        output_file=output,
        force=force,
        workers=workers,
    )

    try:
        result = asyncio.run(bulk_use_case.execute_bulk_config_export(request))
    except ValueError as e:
        console.print(f"[yellow]{e}[/yellow]")
        raise click.Abort() from None

    # Write to output file
    try:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        console.print(f"[green]Configuration exported to {output}")
    except Exception as e:
        console.print(f"[red]Error writing to file: {e}")
        raise click.Abort() from e


@config.command()
@device_targeting_options
@click.option(
    "--component",
    required=True,
    help="Single component type to apply configuration to (e.g., switch, input)",
)
@click.option(
    "--config-file",
    type=click.Path(exists=True),
    help="Path to JSON configuration file",
)
@click.option(
    "--config",
    help="JSON configuration string (alternative to --config-file)",
)
@click.option("--force", is_flag=True, help="Skip confirmation prompts")
@click.option(
    "--workers",
    type=int,
    default=10,
    help="Number of concurrent operations (default: 10)",
)
@click.pass_context
def apply(
    ctx: click.Context,
    from_config: bool,
    devices: tuple[str, ...],
    component: str,
    config_file: str | None,
    config: str | None,
    force: bool,
    workers: int,
) -> None:
    """
    📥 Apply configuration to component type on multiple devices.

    ⚠️  SAFETY WARNING: This will modify device configurations.
    Consider creating backups before applying configurations.

    Examples:
      shelly-manager bulk config apply --from-config --component switch --config-file switch.json
      shelly-manager bulk config apply --devices 192.168.1.100,192.168.1.101 --component switch --config '{"in_mode":"flip"}'
    """
    console = ctx.obj.console
    container = ctx.obj.container

    if not config_file and not config:
        console.print("[red]Error: Either --config-file or --config must be provided.")
        raise click.Abort()

    if config_file and config:
        console.print("[red]Error: Cannot use both --config-file and --config options.")
        raise click.Abort()

    config_data = None
    config_source = ""

    if config_file:
        try:
            with open(config_file) as f:
                config_data = json.load(f)
            config_source = f"file: {config_file}"
        except (FileNotFoundError, json.JSONDecodeError) as e:
            console.print(f"[red]Error reading config file: {e}")
            raise click.Abort() from e
    else:
        try:
            assert config is not None
            config_data = json.loads(config)
            config_source = "command line"
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing config JSON: {e}")
            raise click.Abort() from e

    if not force:
        device_count = len(devices) if devices else "configured"
        console.print(
            f"[yellow]⚠️  You are about to apply configuration to [bold]{component}[/bold] components on [bold]{device_count}[/bold] devices."
        )
        console.print(f"[yellow]Configuration source: {config_source}")
        console.print(f"[yellow]Configuration: {json.dumps(config_data, indent=2)}")

        if not click.confirm("Do you want to continue?"):
            console.print("Operation cancelled.")
            raise click.Abort()

    bulk_use_case = BulkOperationsUseCase(container, console)

    request = BulkConfigApplyRequest(
        devices=list(devices),
        from_config=from_config,
        component_type=component,
        config_file=config_file,
        config_data=config_data,
        force=force,
        workers=workers,
    )

    try:
        results = asyncio.run(bulk_use_case.execute_bulk_config_apply(request))
    except ValueError as e:
        console.print(f"[red]Error: {e}")
        raise click.Abort() from None

    successful = len([r for r in results if r.success])
    failed = len([r for r in results if not r.success])

    console.print(
        f"[green]Configuration applied successfully to {successful} components"
    )
    if failed > 0:
        console.print(f"[red]{failed} components failed")
        for result in results:
            if not result.success:
                console.print(f"[red]  {result.device_ip}: {result.error}")
