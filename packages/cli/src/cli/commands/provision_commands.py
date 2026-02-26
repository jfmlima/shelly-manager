"""CLI commands for device provisioning."""

import click
from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.domain.value_objects.provision_request import (
    DetectDeviceRequest,
    ProvisionDeviceRequest,
)
from rich.panel import Panel
from rich.table import Table

from cli.commands.common import async_command, common_options
from cli.presentation.styles import Messages


@click.group(name="provision")
def provision_commands() -> None:
    """Provision new Shelly devices."""
    pass


# --- Device operations ---


@provision_commands.command("detect")
@click.option(
    "--ip",
    default="192.168.33.1",
    help="Device AP IP address (default: 192.168.33.1)",
)
@common_options
@click.pass_context
@async_command
async def detect_device(
    ctx: click.Context,
    ip: str,
    timeout: float,
    workers: int,
) -> None:
    """Detect a Shelly device at the AP IP address."""
    console = ctx.obj.console
    container = ctx.obj.container

    request = DetectDeviceRequest(device_ip=ip, timeout=timeout)
    use_case = container.get_provision_device_interactor()

    try:
        with console.status(f"Detecting device at {ip}..."):
            info = await use_case.detect(request)
    except Exception as e:
        console.print(Messages.error(f"Detection failed: {e}"))
        raise click.Abort() from None

    table = Table(title="Detected Device", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Device ID", info.device_id)
    table.add_row("Model", info.model)
    table.add_row("App", info.app or "-")
    table.add_row("Generation", str(info.generation))
    table.add_row("MAC", info.mac)
    table.add_row("Firmware", info.firmware_version)
    table.add_row("Auth Enabled", str(info.auth_enabled))

    console.print(table)


@provision_commands.command("run")
@click.option(
    "--ip",
    default="192.168.33.1",
    help="Device AP IP address (default: 192.168.33.1)",
)
@click.option(
    "--profile",
    "profile_name",
    default=None,
    help="Profile name to use (default: use default profile)",
)
@click.option(
    "--verify-targets",
    default=None,
    help="Network targets to scan for verification (e.g., 192.168.1.0/24)",
)
@common_options
@click.pass_context
@async_command
async def run_provision(
    ctx: click.Context,
    ip: str,
    profile_name: str | None,
    verify_targets: str | None,
    timeout: float,
    workers: int,
) -> None:
    """Provision a new Shelly device connected via its AP."""
    console = ctx.obj.console
    container = ctx.obj.container

    # Resolve profile ID from name
    profile_id: int | None = None
    if profile_name:
        profiles_uc = container.get_manage_profiles_interactor()
        profiles = await profiles_uc.list_profiles()
        matched = [p for p in profiles if p.name == profile_name]
        if not matched:
            console.print(Messages.error(f"Profile not found: {profile_name}"))
            raise click.Abort()
        profile_id = matched[0].id

    request = ProvisionDeviceRequest(
        device_ip=ip,
        profile_id=profile_id,
        timeout=timeout,
    )

    use_case = container.get_provision_device_interactor()

    console.print(f"\n[bold]Provisioning device at {ip}...[/bold]\n")

    result = await use_case.execute(request)

    # Display steps
    for step in result.steps_completed:
        icon = "[green]OK[/green]"
        restart = (
            " [yellow](restart required)[/yellow]" if step.restart_required else ""
        )
        console.print(f"  {icon}  {step.name}: {step.message or ''}{restart}")

    for step in result.steps_failed:
        console.print(f"  [red]FAIL[/red]  {step.name}: {step.message or ''}")

    console.print()

    if result.success:
        console.print(
            Panel(
                f"[green]Device provisioned successfully![/green]\n"
                f"Device: {result.device_model or 'unknown'} "
                f"(MAC: {result.device_mac or 'unknown'})",
                title="Provisioning Complete",
            )
        )

        # Verification step
        if result.needs_verification and verify_targets:
            console.print(
                "\n[yellow]Please reconnect to your main network, "
                "then press Enter to verify...[/yellow]"
            )
            click.pause("")

            with console.status("Scanning for device on target network..."):
                found_ip = await use_case.verify(
                    device_mac=result.device_mac or "",
                    scan_targets=[verify_targets],
                    timeout=30.0,
                )

            if found_ip:
                console.print(
                    Messages.success(f"Device found at {found_ip} on target network!")
                )
            else:
                console.print(
                    Messages.warning(
                        "Device not found on target network. "
                        "It may still be connecting. Try a manual scan later."
                    )
                )
        elif result.needs_verification:
            console.print(
                Messages.info(
                    "Reconnect to your main network and run a scan "
                    "to verify the device joined successfully."
                )
            )
    else:
        console.print(
            Panel(
                f"[red]Provisioning failed![/red]\n{result.error or 'Unknown error'}",
                title="Provisioning Failed",
            )
        )
        raise click.Abort()


# --- Profile management ---


@provision_commands.group("profiles")
def profile_commands() -> None:
    """Manage provisioning profiles."""
    pass


@profile_commands.command("list")
@common_options
@click.pass_context
@async_command
async def list_profiles(
    ctx: click.Context,
    timeout: float,
    workers: int,
) -> None:
    """List all provisioning profiles."""
    console = ctx.obj.console
    container = ctx.obj.container

    use_case = container.get_manage_profiles_interactor()
    profiles = await use_case.list_profiles()

    if not profiles:
        console.print(Messages.warning("No provisioning profiles configured."))
        console.print(
            Messages.info("Create one with: shelly-manager provision profiles create")
        )
        return

    table = Table(
        title="Provisioning Profiles", show_header=True, header_style="bold magenta"
    )
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Default", style="green")
    table.add_column("Wi-Fi SSID", style="yellow")
    table.add_column("MQTT", style="blue")
    table.add_column("Auth", style="red")

    for p in profiles:
        table.add_row(
            str(p.id),
            p.name,
            "Yes" if p.is_default else "",
            p.wifi_ssid or "-",
            p.mqtt_server if p.mqtt_enabled else "disabled",
            "set" if p.auth_password else "-",
        )

    console.print(table)


@profile_commands.command("create")
@click.option("--name", required=True, help="Profile name")
@click.option("--wifi-ssid", default=None, help="Wi-Fi SSID")
@click.option("--wifi-password", default=None, help="Wi-Fi password")
@click.option("--mqtt-server", default=None, help="MQTT broker host:port")
@click.option("--mqtt-user", default=None, help="MQTT username")
@click.option("--mqtt-password", default=None, help="MQTT password")
@click.option("--mqtt-topic-template", default=None, help="MQTT topic prefix template")
@click.option("--auth-password", default=None, help="Device auth password")
@click.option("--device-name-template", default=None, help="Device name template")
@click.option("--timezone", default=None, help="Timezone (e.g., Europe/Berlin)")
@click.option("--cloud/--no-cloud", default=False, help="Enable cloud connection")
@click.option(
    "--default/--no-default", "is_default", default=False, help="Set as default profile"
)
@common_options
@click.pass_context
@async_command
async def create_profile(
    ctx: click.Context,
    name: str,
    wifi_ssid: str | None,
    wifi_password: str | None,
    mqtt_server: str | None,
    mqtt_user: str | None,
    mqtt_password: str | None,
    mqtt_topic_template: str | None,
    auth_password: str | None,
    device_name_template: str | None,
    timezone: str | None,
    cloud: bool,
    is_default: bool,
    timeout: float,
    workers: int,
) -> None:
    """Create a new provisioning profile."""
    console = ctx.obj.console
    container = ctx.obj.container

    profile = ProvisioningProfile(
        name=name,
        wifi_ssid=wifi_ssid,
        wifi_password=wifi_password,
        mqtt_enabled=mqtt_server is not None,
        mqtt_server=mqtt_server,
        mqtt_user=mqtt_user,
        mqtt_password=mqtt_password,
        mqtt_topic_prefix_template=mqtt_topic_template,
        auth_password=auth_password,
        device_name_template=device_name_template,
        timezone=timezone,
        cloud_enabled=cloud,
        is_default=is_default,
    )

    use_case = container.get_manage_profiles_interactor()

    try:
        created = await use_case.create_profile(profile)
        console.print(
            Messages.success(
                f"Profile '{created.name}' created (id={created.id})"
                + (" [default]" if created.is_default else "")
            )
        )
    except Exception as e:
        console.print(Messages.error(f"Failed to create profile: {e}"))
        raise click.Abort() from None


@profile_commands.command("delete")
@click.argument("name")
@common_options
@click.pass_context
@async_command
async def delete_profile(
    ctx: click.Context,
    name: str,
    timeout: float,
    workers: int,
) -> None:
    """Delete a provisioning profile by name."""
    console = ctx.obj.console
    container = ctx.obj.container

    use_case = container.get_manage_profiles_interactor()
    profiles = await use_case.list_profiles()
    matched = [p for p in profiles if p.name == name]

    if not matched:
        console.print(Messages.error(f"Profile not found: {name}"))
        raise click.Abort()

    try:
        await use_case.delete_profile(matched[0].id)
        console.print(Messages.success(f"Profile '{name}' deleted"))
    except Exception as e:
        console.print(Messages.error(f"Failed to delete profile: {e}"))
        raise click.Abort() from None


@profile_commands.command("set-default")
@click.argument("name")
@common_options
@click.pass_context
@async_command
async def set_default_profile(
    ctx: click.Context,
    name: str,
    timeout: float,
    workers: int,
) -> None:
    """Set a profile as the default."""
    console = ctx.obj.console
    container = ctx.obj.container

    use_case = container.get_manage_profiles_interactor()
    profiles = await use_case.list_profiles()
    matched = [p for p in profiles if p.name == name]

    if not matched:
        console.print(Messages.error(f"Profile not found: {name}"))
        raise click.Abort()

    try:
        await use_case.set_default_profile(matched[0].id)
        console.print(Messages.success(f"Profile '{name}' set as default"))
    except Exception as e:
        console.print(Messages.error(f"Failed to set default: {e}"))
        raise click.Abort() from None
