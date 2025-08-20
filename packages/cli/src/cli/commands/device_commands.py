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
    validate_ip_range,
)


@click.group()
def device_commands() -> None:
    pass


@device_commands.command()
@click.argument("ip_ranges", nargs=-1, callback=validate_ip_range)
@device_targeting_options
@common_options
@click.pass_context
@async_command
async def scan(
    ctx: click.Context,
    ip_ranges: tuple[str, ...],
    from_config: bool,
    devices: tuple[str, ...],
    timeout: int,
    workers: int,
) -> None:
    """
    🔍 Scan for Shelly devices on the network.

    Discover Shelly devices by scanning IP ranges or using predefined configurations.

    Examples:
      shelly-manager scan 192.168.1.1-192.168.1.50
      shelly-manager scan 192.168.1.0/24
      shelly-manager scan --from-config
      shelly-manager scan --devices 192.168.1.100 --devices 192.168.1.101
    """
    console = ctx.obj.console
    container = ctx.obj.container

    scan_use_case = DeviceScanUseCase(container, console)

    request = DeviceScanRequest(
        ip_ranges=list(ip_ranges),
        from_config=from_config,
        devices=list(devices),
        timeout=timeout,
        workers=workers,
        task_description="Scanning for devices...",
    )

    devices_found = await scan_use_case.execute(request)
    scan_use_case.display_results(devices_found)


@device_commands.command("list")
@click.argument("ip_ranges", nargs=-1, callback=validate_ip_range)
@device_targeting_options
@common_options
@click.pass_context
@async_command
async def list_devices(
    ctx: click.Context,
    ip_ranges: tuple[str, ...],
    from_config: bool,
    devices: tuple[str, ...],
    timeout: int,
    workers: int,
) -> None:
    """
    📋 List Shelly devices with detailed information.

    Similar to scan but optimized for listing known devices with full details.

    Examples:
      shelly-manager list --from-config
      shelly-manager list 192.168.1.1-192.168.1.50
    """
    console = ctx.obj.console
    container = ctx.obj.container

    scan_use_case = DeviceScanUseCase(container, console)

    request = DeviceScanRequest(
        ip_ranges=list(ip_ranges),
        from_config=from_config,
        devices=list(devices),
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
@click.argument("devices", nargs=-1, required=False)
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
    devices: tuple[str, ...],
    from_config: bool,
    include_updates: bool,
    timeout: int,
    workers: int,
) -> None:
    """
    📊 Check status of specific Shelly devices.

    Get detailed status information including firmware versions, update availability,
    and device health metrics.

    Examples:
      shelly-manager status 192.168.1.100 192.168.1.101
      shelly-manager status --from-config
    """
    console = ctx.obj.console
    container = ctx.obj.container

    status_use_case = DeviceStatusUseCase(container, console)

    request = DeviceStatusRequest(
        devices=list(devices),
        from_config=from_config,
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
        console.print("  shelly-manager device status --from-config")
        raise click.Abort() from None


@click.group()
def actions() -> None:
    """🎯 Component actions - execute actions on device components."""
    pass


@actions.command("list")
@device_targeting_options
@click.option("--component-type", help="Filter by component type")
@common_options
@click.pass_context
@async_command
async def list_component_actions(
    ctx: click.Context,
    from_config: bool,
    devices: tuple[str, ...],
    component_type: str | None,
    timeout: int,
    workers: int,
) -> None:
    """📋 List available actions for device components.

    Show all available actions that can be performed on device components.

    Examples:
      shelly-manager device actions list --devices 192.168.1.100
      shelly-manager device actions list --from-config
      shelly-manager device actions list --component-type switch
    """
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    request = ComponentActionsListRequest(
        devices=list(devices),
        from_config=from_config,
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
        console.print("  shelly-manager device actions list --devices 192.168.1.100")
        console.print("  shelly-manager device actions list --from-config")
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
    devices: tuple[str, ...],
    from_config: bool,
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🎯 Execute action on device components.

    Execute any available action on device components.

    Examples:
      shelly-manager device actions execute shelly Reboot --devices 192.168.1.100
      shelly-manager device actions execute switch:0 Toggle --from-config
    """
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    request = ComponentActionRequest(
        devices=list(devices),
        from_config=from_config,
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
            "  shelly-manager device actions execute shelly Reboot --devices 192.168.1.100"
        )
        console.print(
            "  shelly-manager device actions execute switch:0 Toggle --from-config"
        )
        raise click.Abort() from None
    except RuntimeError:
        return


device_commands.add_command(actions)


@device_commands.command("reboot")
@device_targeting_options
@click.option("--force", is_flag=True)
@common_options
@click.pass_context
@async_command
async def reboot_devices(
    ctx: click.Context,
    from_config: bool,
    devices: tuple[str, ...],
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🔄 Reboot devices (shortcut for: actions execute shelly Reboot).

    Examples:
      shelly-manager device reboot --devices 192.168.1.100
      shelly-manager device reboot --from-config --force
    """
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    request = ComponentActionRequest(
        devices=list(devices),
        from_config=from_config,
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
        console.print("  shelly-manager device reboot --devices 192.168.1.100")
        console.print("  shelly-manager device reboot --from-config --force")
        raise click.Abort() from None
    except RuntimeError:
        return


@device_commands.command("update")
@device_targeting_options
@click.option("--channel", type=click.Choice(["stable", "beta"]), default="stable")
@click.option("--force", is_flag=True)
@common_options
@click.pass_context
@async_command
async def update_firmware(
    ctx: click.Context,
    from_config: bool,
    devices: tuple[str, ...],
    channel: str,
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🚀 Update device firmware (shortcut for: actions execute shelly Update).

    Examples:
      shelly-manager device update --devices 192.168.1.100
      shelly-manager device update --from-config --channel beta
    """
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    update_parameters = {}
    if channel != "stable":
        update_parameters["channel"] = channel

    request = ComponentActionRequest(
        devices=list(devices),
        from_config=from_config,
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
        console.print("  shelly-manager device update --devices 192.168.1.100")
        console.print("  shelly-manager device update --from-config --channel beta")
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
    from_config: bool,
    devices: tuple[str, ...],
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """🔄 Toggle switch component (shortcut for: actions execute switch:X Toggle).

    Examples:
      shelly-manager device toggle switch:0 --devices 192.168.1.100
      shelly-manager device toggle switch:1 --from-config
    """
    console = ctx.obj.console
    container = ctx.obj.container

    actions_use_case = ComponentActionsUseCase(container, console)

    request = ComponentActionRequest(
        devices=list(devices),
        from_config=from_config,
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
        console.print("  shelly-manager device toggle switch:0 --devices 192.168.1.100")
        console.print("  shelly-manager device toggle switch:1 --from-config")
        raise click.Abort() from None
    except RuntimeError:
        return


__all__ = ["device_commands", "scan"]
