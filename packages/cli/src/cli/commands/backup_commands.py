"""CLI commands for device configuration backup and restore."""

from datetime import UTC, datetime

import click
from core.domain.entities.backup_schedule import BackupSchedule
from core.utils.validation import normalize_mac
from rich.table import Table

from cli.commands.common import async_command
from cli.presentation.styles import Messages

EVERY_PRESETS: dict[str, int] = {
    "hourly": 3600,
    "daily": 86400,
    "weekly": 604800,
}


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


@backup_commands.group("schedule")
def backup_schedule() -> None:
    """⏰ Manage automated backup schedules."""
    pass


@backup_schedule.command("create")
@click.option("--name", required=True, help="Unique schedule name")
@click.option(
    "--every",
    type=click.Choice(sorted(EVERY_PRESETS)),
    default=None,
    help="Preset cadence (alternative to --interval-seconds)",
)
@click.option(
    "--interval-seconds",
    type=int,
    default=None,
    help="Custom cadence in seconds (minimum 60)",
)
@click.option(
    "--target",
    "-t",
    "targets",
    multiple=True,
    help="Target device IP, range, or CIDR (repeatable). Ranges and CIDR are "
    "scanned for live devices at run time.",
)
@click.option(
    "--mac",
    "macs",
    multiple=True,
    help="Target device MAC, resolved via last-seen IP (repeatable)",
)
@click.option(
    "--all-credentialed",
    is_flag=True,
    help="Target every device we hold credentials for",
)
@click.option(
    "--keep-last",
    type=int,
    default=None,
    help="Retention: keep only the newest N scheduled backups per device",
)
@click.option(
    "--max-age-days",
    type=int,
    default=None,
    help="Retention: drop scheduled backups older than N days",
)
@click.option("--disabled", is_flag=True, help="Create the schedule disabled")
@click.pass_context
@async_command
async def create_schedule(
    ctx: click.Context,
    name: str,
    every: str | None,
    interval_seconds: int | None,
    targets: tuple[str, ...],
    macs: tuple[str, ...],
    all_credentialed: bool,
    keep_last: int | None,
    max_age_days: int | None,
    disabled: bool,
) -> None:
    """Create an automated backup schedule."""
    console = ctx.obj.console

    if (every is None) == (interval_seconds is None):
        console.print(
            Messages.error("Provide exactly one of --every or --interval-seconds")
        )
        raise click.Abort()
    if interval_seconds is not None and interval_seconds < 60:
        console.print(Messages.error("--interval-seconds must be at least 60"))
        raise click.Abort()
    if not (targets or macs or all_credentialed):
        console.print(
            Messages.error(
                "Provide at least one of --target, --mac, or --all-credentialed"
            )
        )
        raise click.Abort()

    interval = EVERY_PRESETS[every] if every is not None else interval_seconds
    schedule = BackupSchedule(
        name=name,
        interval_seconds=interval,  # type: ignore[arg-type]
        target_ips=list(targets),
        target_macs=[normalize_mac(mac) for mac in macs],
        all_credentialed=all_credentialed,
        enabled=not disabled,
        retention_keep_last=keep_last,
        retention_max_age_days=max_age_days,
    )

    use_case = ctx.obj.container.get_manage_backup_schedules_interactor()
    try:
        created = await use_case.create_schedule(schedule)
    except Exception as e:
        console.print(Messages.error(f"Failed to create schedule: {e}"))
        raise click.Abort() from None

    state = "enabled" if created.enabled else "disabled"
    console.print(
        f"✅ Created schedule [bold]#{created.id}[/bold] "
        f"[cyan]{created.name}[/cyan] ({state}, every {_format_interval(created.interval_seconds)})"
    )


@backup_schedule.command("list")
@click.pass_context
@async_command
async def list_schedules(ctx: click.Context) -> None:
    """List backup schedules."""
    console = ctx.obj.console
    use_case = ctx.obj.container.get_manage_backup_schedules_interactor()

    schedules = await use_case.list_schedules()
    if not schedules:
        console.print(Messages.warning("No backup schedules configured."))
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("Every", style="blue")
    table.add_column("Targets")
    table.add_column("Enabled")
    table.add_column("Next run (UTC)")
    table.add_column("Last status")

    for s in schedules:
        table.add_row(
            str(s.id),
            s.name,
            _format_interval(s.interval_seconds),
            _format_targets(s),
            "✅" if s.enabled else "⛔",
            _format_ts(s.next_run_at),
            s.last_status or "-",
        )

    console.print(table)


@backup_schedule.command("enable")
@click.argument("schedule_id", type=int)
@click.pass_context
@async_command
async def enable_schedule(ctx: click.Context, schedule_id: int) -> None:
    """Enable a backup schedule."""
    await _set_enabled(ctx, schedule_id, True)


@backup_schedule.command("disable")
@click.argument("schedule_id", type=int)
@click.pass_context
@async_command
async def disable_schedule(ctx: click.Context, schedule_id: int) -> None:
    """Disable a backup schedule."""
    await _set_enabled(ctx, schedule_id, False)


@backup_schedule.command("delete")
@click.argument("schedule_id", type=int)
@click.option("--force", is_flag=True, help="Skip the confirmation prompt.")
@click.pass_context
@async_command
async def delete_schedule(ctx: click.Context, schedule_id: int, force: bool) -> None:
    """Delete a backup schedule."""
    console = ctx.obj.console
    if not force:
        click.confirm(f"Delete schedule #{schedule_id}?", abort=True)

    use_case = ctx.obj.container.get_manage_backup_schedules_interactor()
    try:
        await use_case.delete_schedule(schedule_id)
        console.print(f"✅ Deleted schedule [bold]#{schedule_id}[/bold]")
    except Exception as e:
        console.print(Messages.error(f"Failed to delete schedule: {e}"))
        raise click.Abort() from None


@backup_schedule.command("run")
@click.argument("schedule_id", type=int)
@click.pass_context
@async_command
async def run_schedule(ctx: click.Context, schedule_id: int) -> None:
    """Run a backup schedule now, ignoring its next run time."""
    console = ctx.obj.console
    use_case = ctx.obj.container.get_run_due_backups_interactor()

    try:
        result = await use_case.run_schedule(schedule_id)
    except Exception as e:
        console.print(Messages.error(f"Failed to run schedule: {e}"))
        raise click.Abort() from None

    summary = (
        f"{result.ok} ok, {result.failed} failed, {result.skipped} skipped "
        f"across {result.targets} target(s)"
    )
    if result.status in ("ok", "skipped", "empty"):
        console.print(f"✅ Schedule '{result.schedule_name}' run: {summary}")
    else:
        console.print(
            Messages.warning(
                f"Schedule '{result.schedule_name}' finished with issues: {summary}"
            )
        )
        ctx.exit(1)


async def _set_enabled(ctx: click.Context, schedule_id: int, enabled: bool) -> None:
    console = ctx.obj.console
    use_case = ctx.obj.container.get_manage_backup_schedules_interactor()
    try:
        updated = await use_case.set_enabled(schedule_id, enabled)
    except Exception as e:
        console.print(Messages.error(f"Failed to update schedule: {e}"))
        raise click.Abort() from None
    state = "enabled" if updated.enabled else "disabled"
    console.print(f"✅ Schedule [bold]#{schedule_id}[/bold] {state}")


def _format_interval(seconds: int) -> str:
    for name, preset in EVERY_PRESETS.items():
        if seconds == preset:
            return name
    return f"{seconds}s"


def _format_targets(schedule: BackupSchedule) -> str:
    parts: list[str] = []
    if schedule.all_credentialed:
        parts.append("all-credentialed")
    if schedule.target_ips:
        parts.append(f"{len(schedule.target_ips)} ip(s)")
    if schedule.target_macs:
        parts.append(f"{len(schedule.target_macs)} mac(s)")
    return ", ".join(parts) or "-"


def _format_ts(ts: int | None) -> str:
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M")
