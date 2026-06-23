"""CLI commands for device configuration backup and restore."""

from datetime import UTC, datetime

import click
from rich.table import Table

from cli.commands.common import async_command
from cli.presentation.styles import Messages


@click.group(name="backup")
def backup_commands() -> None:
    """💾 Back up and restore device configurations."""
    pass


@backup_commands.command("create")
@click.option("--target", "-t", required=True, help="Device IP address")
@click.option("--name", default=None, help="Optional backup label")
@click.pass_context
@async_command
async def create_backup(ctx: click.Context, target: str, name: str | None) -> None:
    """Capture a full configuration backup of a device."""
    console = ctx.obj.console
    use_case = ctx.obj.container.get_backup_device_config_interactor()

    try:
        backup = await use_case.create_backup(device_ip=target, name=name)
    except Exception as e:
        console.print(Messages.error(f"Backup failed: {e}"))
        raise click.Abort() from None

    console.print(
        f"✅ Backup [bold]#{backup.id}[/bold] created for "
        f"[cyan]{backup.device_name or target}[/cyan] "
        f"(mac=[yellow]{backup.device_mac}[/yellow], {backup.size_bytes} bytes)"
    )


@backup_commands.command("list")
@click.option("--mac", default=None, help="Filter by device MAC address")
@click.pass_context
@async_command
async def list_backups(ctx: click.Context, mac: str | None) -> None:
    """List stored backups, newest first."""
    console = ctx.obj.console
    use_case = ctx.obj.container.get_backup_device_config_interactor()

    summaries = await use_case.list_backups(mac)
    if not summaries:
        console.print(Messages.warning("No backups stored."))
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Device", style="green")
    table.add_column("MAC", style="yellow")
    table.add_column("Gen", style="blue")
    table.add_column("Source")
    table.add_column("Created (UTC)")

    for s in summaries:
        created = (
            datetime.fromtimestamp(s.created_at, tz=UTC).strftime("%Y-%m-%d %H:%M")
            if s.created_at
            else "-"
        )
        table.add_row(
            str(s.id),
            s.name or s.device_name or s.device_ip or "-",
            s.device_mac,
            s.generation,
            s.source,
            created,
        )

    console.print(table)


@backup_commands.command("restore")
@click.argument("backup_id", type=int)
@click.option("--target", "-t", required=True, help="Target device IP address")
@click.option(
    "--component",
    "components",
    multiple=True,
    help="Component key to restore (repeatable). Omit for all non-network components.",
)
@click.option(
    "--all",
    "restore_all",
    is_flag=True,
    help="Include network components (wifi/eth/mqtt/ws/cloud) too.",
)
@click.option(
    "--allow-mac-mismatch",
    is_flag=True,
    help="Restore even if the target MAC differs from the backup.",
)
@click.option("--reboot", is_flag=True, help="Reboot the device after restore.")
@click.option("--force", is_flag=True, help="Skip the confirmation prompt.")
@click.pass_context
@async_command
async def restore_backup(
    ctx: click.Context,
    backup_id: int,
    target: str,
    components: tuple[str, ...],
    restore_all: bool,
    allow_mac_mismatch: bool,
    reboot: bool,
    force: bool,
) -> None:
    """Restore a backup onto a device."""
    console = ctx.obj.console
    use_case = ctx.obj.container.get_restore_device_config_interactor()

    component_keys: list[str] | None = list(components) if components else None
    if restore_all and component_keys is None:
        # Explicitly opt in to network components: select everything in the backup.
        backup_uc = ctx.obj.container.get_backup_device_config_interactor()
        try:
            backup = await backup_uc.get_backup(backup_id)
        except Exception as e:
            console.print(Messages.error(f"Restore failed: {e}"))
            raise click.Abort() from None
        component_keys = list(backup.snapshot.get("components", {}).keys())

    if not force:
        console.print(
            f"⚠️  About to restore backup [bold]#{backup_id}[/bold] onto "
            f"[cyan]{target}[/cyan]. This overwrites device configuration."
        )
        click.confirm("Continue?", abort=True)

    try:
        result = await use_case.restore(
            backup_id,
            target,
            component_keys=component_keys,
            allow_mac_mismatch=allow_mac_mismatch,
            reboot=reboot,
        )
    except Exception as e:
        console.print(Messages.error(f"Restore failed: {e}"))
        raise click.Abort() from None

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Action")
    table.add_column("Result")
    table.add_column("Detail")

    for c in result.components:
        if c.skipped:
            status = "[dim]skipped[/dim]"
            detail = c.skipped_reason or ""
        elif c.success:
            status = "[green]ok[/green]"
            detail = ""
        else:
            status = "[red]failed[/red]"
            detail = c.error or ""
        table.add_row(c.key, c.action, status, detail)

    console.print(table)
    summary = f"{result.succeeded} ok, {result.failed} failed, {result.skipped} skipped"
    if result.success:
        console.print(f"✅ Restore complete: {summary}")
    else:
        console.print(Messages.warning(f"Restore finished with issues: {summary}"))
        ctx.exit(1)


@backup_commands.command("delete")
@click.argument("backup_id", type=int)
@click.pass_context
@async_command
async def delete_backup(ctx: click.Context, backup_id: int) -> None:
    """Delete a stored backup."""
    console = ctx.obj.console
    use_case = ctx.obj.container.get_backup_device_config_interactor()

    try:
        await use_case.delete_backup(backup_id)
        console.print(f"✅ Deleted backup [bold]#{backup_id}[/bold]")
    except Exception as e:
        console.print(Messages.error(f"Failed to delete backup: {e}"))
        raise click.Abort() from None
