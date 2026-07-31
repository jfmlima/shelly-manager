"""
Device-related Click commands.
"""

import sys

import click
from core.domain.enums.enums import UpdateChannel
from rich.console import Console
from rich.markup import escape

from ..entities import (
    ComponentActionRequest,
    ComponentActionsListRequest,
    DeviceScanRequest,
    DeviceStatusRequest,
)
from ..exceptions import EXIT_USAGE, EXIT_VALIDATION
from ..presentation.styles import Messages
from ..use_cases.device.component_actions import ComponentActionsUseCase
from ..use_cases.device.device_status import DeviceStatusUseCase
from ..use_cases.device.scan_devices import DeviceScanUseCase
from .common import (
    async_command,
    common_options,
    device_targeting_options,
)


@click.group()
def device_commands() -> None:
    pass


@device_commands.command()
@click.argument("targets", nargs=-1)
@click.option("--use-mdns", is_flag=True, help="Use mDNS to discover devices")
@device_targeting_options
@common_options
@click.pass_context
@async_command
async def scan(
    ctx: click.Context,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    use_mdns: bool,
    timeout: int,
    workers: int,
) -> None:
    """
    Discover Shelly devices by scanning IP targets or using mDNS.

    Examples:
      shelly-manager scan 192.168.1.1-50
      shelly-manager scan 192.168.1.0/24
      shelly-manager scan -t 192.168.1.100 -t 192.168.1.101
      shelly-manager scan --use-mdns
    """
    console = ctx.obj.console
    container = ctx.obj.container

    scan_use_case = DeviceScanUseCase(container, console)

    request = DeviceScanRequest(
        targets=list(targets) + list(targets_opt),
        timeout=timeout,
        workers=workers,
        use_mdns=use_mdns,
        task_description="Scanning for devices...",
    )

    devices_found = await scan_use_case.execute(request)
    scan_use_case.display_results(devices_found)


@device_commands.command("list")
@click.argument("targets", nargs=-1)
@device_targeting_options
@common_options
@click.pass_context
@async_command
async def list_devices(
    ctx: click.Context,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    timeout: int,
    workers: int,
) -> None:
    """
    Similar to scan but optimized for listing known devices with full details in a table format.

    Examples:
      shelly-manager list 192.168.1.0/24
      shelly-manager list -t 192.168.1.100 -t 192.168.1.101
    """
    console = ctx.obj.console
    container = ctx.obj.container

    scan_use_case = DeviceScanUseCase(container, console)

    request = DeviceScanRequest(
        targets=list(targets) + list(targets_opt),
        timeout=timeout,
        workers=workers,
        task_description="Listing devices...",
    )

    devices_found = await scan_use_case.execute(request)

    if devices_found:
        scan_use_case.display_results(devices_found, show_table=True)
    else:
        console.print(f"\n{Messages.warning('No devices found')}")


@device_commands.command()
@click.argument("targets", nargs=-1, required=False)
@device_targeting_options
@common_options
@click.pass_context
@async_command
async def status(
    ctx: click.Context,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    timeout: int,
    workers: int,
) -> None:
    """
    Get detailed status information including firmware versions, update availability,
    and device health metrics.

    Examples:
      shelly-manager status 192.168.1.100 192.168.1.101
      shelly-manager status -t 192.168.1.0/24
    """
    console = ctx.obj.console
    container = ctx.obj.container

    status_use_case = DeviceStatusUseCase(container, console)

    request = DeviceStatusRequest(
        targets=list(targets) + list(targets_opt),
        timeout=timeout,
        workers=workers,
        verbose=ctx.obj.verbose,
    )

    try:
        results = await status_use_case.execute(request)
    except ValueError as e:
        _print_usage_error(
            console,
            e,
            "shelly-manager device status 192.168.1.100 192.168.1.101",
            "shelly-manager device status 192.168.1.0/24",
        )
        sys.exit(EXIT_VALIDATION)
    status_use_case.display_results(results)


@click.group()
def actions() -> None:
    """🎯 Component actions - execute actions on device components."""
    pass


@actions.command("list")
@click.argument("targets", nargs=-1)
@device_targeting_options
@click.option("--component-type", help="Filter by component type")
@common_options
@click.pass_context
@async_command
async def list_component_actions(
    ctx: click.Context,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    component_type: str | None,
    timeout: int,
    workers: int,
) -> None:
    """📋 List available actions for device components.

    Show all available actions that can be performed on device components.

    Examples:
      shelly-manager device actions list -t 192.168.1.100
      shelly-manager device actions list 192.168.1.0/24
      shelly-manager device actions list -t 192.168.1.100 --component-type switch
    """
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    request = ComponentActionsListRequest(
        targets=list(targets) + list(targets_opt),
        timeout=timeout,
        workers=workers,
        component_type=component_type,
    )

    try:
        results = await actions_use_case.list_actions(request)
    except ValueError as e:
        _print_usage_error(
            console,
            e,
            "shelly-manager device actions list -t 192.168.1.100",
            "shelly-manager device actions list 192.168.1.0/24",
        )
        sys.exit(EXIT_VALIDATION)
    actions_use_case.display_actions_list(results)


@actions.command("execute")
@click.argument("component_key")
@click.argument("action")
@device_targeting_options
@click.option("--force", is_flag=True, help="Skip confirmation")
@common_options
@click.pass_context
@async_command
async def execute_component_action(
    ctx: click.Context,
    component_key: str,
    action: str,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🎯 Execute action on device components.

    Execute any available action on device components.

    The action may be bare or carry the namespace that "actions list" prints.

    Examples:
      shelly-manager device actions execute shelly Reboot -t 192.168.1.100
      shelly-manager device actions execute switch:0 Toggle -t 192.168.1.100
      shelly-manager device actions execute switch:0 Switch.Toggle -t 192.168.1.100
    """
    request = ComponentActionRequest(
        targets=list(targets) + list(targets_opt),
        component_key=component_key,
        action=action,
        timeout=timeout,
        workers=workers,
        force=force,
    )

    await _run_component_action(
        ctx,
        request,
        "shelly-manager device actions execute shelly Reboot -t 192.168.1.100",
        "shelly-manager device actions execute switch:0 Toggle -t 192.168.1.0/24",
    )


device_commands.add_command(actions)


@device_commands.command("reboot")
@click.argument("targets", nargs=-1)
@device_targeting_options
@click.option("--force", is_flag=True)
@common_options
@click.pass_context
@async_command
async def reboot_devices(
    ctx: click.Context,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🔄 Reboot devices (shortcut for: actions execute shelly Reboot).

    Examples:
      shelly-manager device reboot -t 192.168.1.100
      shelly-manager device reboot 192.168.1.0/24 --force
    """
    request = ComponentActionRequest(
        targets=list(targets) + list(targets_opt),
        component_key="shelly",
        action="Reboot",
        timeout=timeout,
        workers=workers,
        force=force,
    )

    await _run_component_action(
        ctx,
        request,
        "shelly-manager device reboot -t 192.168.1.100",
        "shelly-manager device reboot 192.168.1.0/24 --force",
    )


@device_commands.command("update")
@click.argument("targets", nargs=-1)
@device_targeting_options
@click.option(
    "--channel",
    type=click.Choice([channel.value for channel in UpdateChannel]),
    default=UpdateChannel.STABLE.value,
)
@click.option(
    "--source",
    type=click.Choice(["internet", "local"]),
    default="internet",
    help=(
        "Where the device fetches firmware from: internet (device downloads "
        "from Shelly) or local (cached in this host's firmware store and "
        "served to the device by the manager API, which must share it)"
    ),
)
@click.option("--force", is_flag=True)
@common_options
@click.pass_context
@async_command
async def update_firmware(
    ctx: click.Context,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    channel: str,
    source: str,
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🚀 Update device firmware (shortcut for: actions execute shelly Update).

    Examples:
      shelly-manager device update -t 192.168.1.100
      shelly-manager device update 192.168.1.0/24 --channel beta
      shelly-manager device update -t 192.168.1.100 --source local
    """
    if source == "local" and channel != UpdateChannel.STABLE.value:
        ctx.obj.console.print(
            Messages.error("Local updates support the stable channel only")
        )
        sys.exit(EXIT_USAGE)

    request = ComponentActionRequest(
        targets=list(targets) + list(targets_opt),
        component_key="shelly",
        action="Update",
        parameters=UpdateChannel(channel).to_update_parameters(),
        timeout=timeout,
        workers=workers,
        force=force,
    )

    await _run_component_action(
        ctx,
        request,
        "shelly-manager device update -t 192.168.1.100",
        "shelly-manager device update 192.168.1.0/24 --channel beta",
        from_local_store=source == "local",
    )


@device_commands.command("toggle")
@click.argument("component_key")
@device_targeting_options
@click.option("--force", is_flag=True)
@common_options
@click.pass_context
@async_command
async def toggle_component(
    ctx: click.Context,
    component_key: str,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🔄 Toggle switch component (shortcut for: actions execute switch:X Toggle).

    Examples:
      shelly-manager device toggle switch:0 -t 192.168.1.100
      shelly-manager device toggle switch:1 192.168.1.0/24
    """
    request = ComponentActionRequest(
        targets=list(targets) + list(targets_opt),
        component_key=component_key,
        action="Toggle",
        timeout=timeout,
        workers=workers,
        force=force,
    )

    await _run_component_action(
        ctx,
        request,
        "shelly-manager device toggle switch:0 -t 192.168.1.100",
        "shelly-manager device toggle switch:1 192.168.1.0/24",
    )


def _print_usage_error(console: Console, error: Exception, *examples: str) -> None:
    console.print(Messages.error(escape(str(error))))
    console.print("\nExamples:")
    for example in examples:
        console.print(f"  {example}")


async def _run_component_action(
    ctx: click.Context,
    request: ComponentActionRequest,
    *examples: str,
    from_local_store: bool = False,
) -> None:
    """Run one component action across every requested device.

    ``from_local_store`` serves a firmware update out of this host's own
    firmware store rather than leaving each device to fetch from the internet.
    """
    console = ctx.obj.console
    actions_use_case = ComponentActionsUseCase(ctx.obj.container, console)
    execute = (
        actions_use_case.execute_local_update
        if from_local_store
        else actions_use_case.execute_action
    )
    try:
        results = await execute(request)
    except ValueError as e:
        _print_usage_error(console, e, *examples)
        sys.exit(EXIT_VALIDATION)
    actions_use_case.display_action_results(results)


__all__ = ["device_commands", "scan"]
