"""
Device-related Click commands.
"""

import click

from ..entities import (
    DeviceConfigUpdateRequest,
    DeviceRebootRequest,
    DeviceScanRequest,
    DeviceStatusRequest,
    FirmwareUpdateRequest,
)
from ..presentation.styles import Messages
from ..use_cases.device.config_update import ConfigUpdateUseCase
from ..use_cases.device.device_reboot import DeviceRebootUseCase
from ..use_cases.device.device_status import DeviceStatusUseCase
from ..use_cases.device.firmware_update import FirmwareUpdateUseCase
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


@device_commands.command()
@click.argument("devices", nargs=-1, required=False)
@device_targeting_options
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@common_options
@click.pass_context
@async_command
async def reboot(
    ctx: click.Context,
    devices: tuple[str, ...],
    from_config: bool,
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """
    🔄 Reboot Shelly devices.

    Safely reboot one or more Shelly devices. Shows confirmation prompt
    unless --force is used.

    Examples:
      shelly-manager reboot 192.168.1.100
      shelly-manager reboot --from-config --force
    """
    console = ctx.obj.console
    container = ctx.obj.container

    reboot_use_case = DeviceRebootUseCase(container, console)

    request = DeviceRebootRequest(
        devices=list(devices),
        from_config=from_config,
        force=force,
        timeout=timeout,
        workers=workers,
    )

    try:
        results = await reboot_use_case.execute(request)
        reboot_use_case.display_results(results)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        console.print("\nExamples:")
        console.print("  shelly-manager device reboot 192.168.1.100 192.168.1.101")
        console.print("  shelly-manager device reboot --from-config")
        raise click.Abort() from None
    except RuntimeError:
        return


@click.group()
def update() -> None:
    """Device update operations."""
    pass


@update.command()
@click.argument("devices", nargs=-1)
@device_targeting_options
@click.option(
    "--channel",
    type=click.Choice(["stable", "beta"], case_sensitive=False),
    default="stable",
    help="Firmware update channel",
)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--check-only", is_flag=True, help="Only check for updates, do not install"
)
@common_options
@click.pass_context
@async_command
async def firmware(
    ctx: click.Context,
    devices: tuple[str, ...],
    from_config: bool,
    channel: str,
    force: bool,
    check_only: bool,
    timeout: int,
    workers: int,
) -> None:
    """
    🚀 Update Shelly device firmware.

    Update device firmware to the latest version from the specified channel.
    Supports both individual devices and batch operations.

    Examples:
      shelly-manager device update firmware 192.168.1.100
      shelly-manager device update firmware --from-config --channel beta
      shelly-manager device update firmware 192.168.1.100 192.168.1.101 --check-only
    """
    console = ctx.obj.console
    container = ctx.obj.container

    request = FirmwareUpdateRequest(
        devices=list(devices),
        from_config=from_config,
        channel=channel,
        force=force,
        check_only=check_only,
        timeout=timeout,
        workers=workers,
    )

    try:
        firmware_update_use_case = FirmwareUpdateUseCase(container, console)
        await firmware_update_use_case.execute(request)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        raise click.Abort() from None
    except RuntimeError:
        raise click.Abort() from None


@update.command()
@click.argument("devices", nargs=-1)
@device_targeting_options
@click.option(
    "--config-file",
    type=click.Path(exists=True),
    help="Configuration file to apply to devices",
)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@common_options
@click.pass_context
@async_command
async def config(
    ctx: click.Context,
    devices: tuple[str, ...],
    from_config: bool,
    config_file: str,
    force: bool,
    timeout: int,
    workers: int,
) -> None:
    """
    ⚙️ Update Shelly device configuration.

    Apply configuration changes to devices. Can use a specific config file
    or apply predefined configurations.

    Examples:
      shelly-manager device update config 192.168.1.100 --config-file my-config.json
      shelly-manager device update config --from-config
      shelly-manager device update config 192.168.1.100 192.168.1.101
    """
    console = ctx.obj.console
    container = ctx.obj.container

    request = DeviceConfigUpdateRequest(
        devices=list(devices),
        from_config=from_config,
        config_file=config_file,
        force=force,
        timeout=timeout,
        workers=workers,
    )

    try:
        config_update_use_case = ConfigUpdateUseCase(container, console)
        await config_update_use_case.execute(request)
    except ValueError as e:
        console.print(Messages.error(str(e)))
        raise click.Abort() from None
    except RuntimeError:
        raise click.Abort() from None


device_commands.add_command(update)


__all__ = ["device_commands", "scan"]
