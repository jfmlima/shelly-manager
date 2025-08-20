"""
Bulk operations commands for the CLI.
"""

import asyncio

import click

from cli.commands.common import device_targeting_options
from cli.entities.bulk import BulkOperationRequest, BulkRebootRequest
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
