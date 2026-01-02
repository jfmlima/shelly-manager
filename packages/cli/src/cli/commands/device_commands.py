"""
Device-related Click commands.
"""

import click

from ..entities import (
    ComponentActionRequest,
    ComponentActionsListRequest,
    DeviceScanRequest,
    DeviceStatusRequest,
)
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
@click.option(
    "--include-updates",
    is_flag=True,
    default=True,
    help="Include firmware update information",
)
@click.pass_context
@async_command
async def status(
    ctx: click.Context,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    include_updates: bool,
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
        include_updates=include_updates,
        timeout=timeout,
        workers=workers,
        verbose=ctx.obj.verbose,
    )

    try:
        results = await status_use_case.execute(request)
        status_use_case.display_results(results)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        console.print("\nExamples:")
        console.print("  shelly-manager device status 192.168.1.100 192.168.1.101")
        console.print("  shelly-manager device status 192.168.1.0/24")
        raise click.Abort() from None


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
        actions_use_case.display_actions_list(results)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        console.print("\nExamples:")
        console.print("  shelly-manager device actions list -t 192.168.1.100")
        console.print("  shelly-manager device actions list 192.168.1.0/24")
        raise click.Abort() from None


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

    Examples:
      shelly-manager device actions execute shelly Reboot -t 192.168.1.100
      shelly-manager device actions execute switch:0 Toggle -t 192.168.1.100
    """
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    request = ComponentActionRequest(
        targets=list(targets) + list(targets_opt),
        component_key=component_key,
        action=action,
        timeout=timeout,
        workers=workers,
        force=force,
    )

    try:
        results = await actions_use_case.execute_action(request)
        actions_use_case.display_action_results(results)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        console.print("\nExamples:")
        console.print(
            "  shelly-manager device actions execute shelly Reboot -t 192.168.1.100"
        )
        console.print(
            "  shelly-manager device actions execute switch:0 Toggle -t 192.168.1.0/24"
        )
        raise click.Abort() from None
    except RuntimeError:
        return


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
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    request = ComponentActionRequest(
        targets=list(targets) + list(targets_opt),
        component_key="shelly",
        action="Reboot",
        timeout=timeout,
        workers=workers,
        force=force,
    )

    try:
        results = await actions_use_case.execute_action(request)
        actions_use_case.display_action_results(results)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        console.print("\nExamples:")
        console.print("  shelly-manager device reboot -t 192.168.1.100")
        console.print("  shelly-manager device reboot 192.168.1.0/24 --force")
        raise click.Abort() from None
    except RuntimeError:
        return


@device_commands.command("update")
@click.argument("targets", nargs=-1)
@device_targeting_options
@click.option("--channel", type=click.Choice(["stable", "beta"]), default="stable")
@click.option("--force", is_flag=True)
@common_options
@click.pass_context
@async_command
async def update_firmware(
    ctx: click.Context,
    targets: tuple[str, ...],
    targets_opt: tuple[str, ...],
    channel: str,
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🚀 Update device firmware (shortcut for: actions execute shelly Update).

    Examples:
      shelly-manager device update -t 192.168.1.100
      shelly-manager device update 192.168.1.0/24 --channel beta
    """
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    update_parameters = {}
    if channel != "stable":
        update_parameters["channel"] = channel

    request = ComponentActionRequest(
        targets=list(targets) + list(targets_opt),
        component_key="shelly",
        action="Update",
        parameters=update_parameters,
        timeout=timeout,
        workers=workers,
        force=force,
    )

    try:
        results = await actions_use_case.execute_action(request)
        actions_use_case.display_action_results(results)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        console.print("\nExamples:")
        console.print("  shelly-manager device update -t 192.168.1.100")
        console.print("  shelly-manager device update 192.168.1.0/24 --channel beta")
        raise click.Abort() from None
    except RuntimeError:
        return


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
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    request = ComponentActionRequest(
        targets=list(targets) + list(targets_opt),
        component_key=component_key,
        action="Toggle",
        timeout=timeout,
        workers=workers,
        force=force,
    )

    try:
        results = await actions_use_case.execute_action(request)
        actions_use_case.display_action_results(results)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        console.print("\nExamples:")
        console.print("  shelly-manager device toggle switch:0 -t 192.168.1.100")
        console.print("  shelly-manager device toggle switch:1 192.168.1.0/24")
        raise click.Abort() from None
    except RuntimeError:
        return


__all__ = ["device_commands", "scan"]
