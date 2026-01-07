import click
from rich.table import Table

from cli.commands.common import async_command, common_options
from cli.presentation.styles import Messages


@click.group(name="credentials")
def credential_commands() -> None:
    """🔐 Manage device credentials."""
    pass


@credential_commands.command("set")
@click.argument("mac")
@click.argument("password")
@click.option("--username", default="admin", help="Username (default: admin)")
@common_options
@click.pass_context
@async_command
async def set_credential(
    ctx: click.Context,
    mac: str,
    password: str,
    username: str,
) -> None:
    """Set credentials for a specific device."""
    console = ctx.obj.console
    container = ctx.obj.container
    repo = container.get_credentials_repository()

    try:
        await repo.set(mac, username, password)
        console.print(f"✅ Credentials set for [bold]{mac.upper()}[/bold]")
    except Exception as e:
        console.print(Messages.error(f"Failed to set credentials: {e}"))
        raise click.Abort() from None


@credential_commands.command("set-global")
@click.argument("password")
@click.option("--username", default="admin", help="Username (default: admin)")
@common_options
@click.pass_context
@async_command
async def set_global_credential(
    ctx: click.Context,
    password: str,
    username: str,
) -> None:
    """Set global fallback credentials."""
    console = ctx.obj.console
    container = ctx.obj.container
    repo = container.get_credentials_repository()

    try:
        await repo.set("*", username, password)
        console.print("✅ Global fallback credentials set")
    except Exception as e:
        console.print(Messages.error(f"Failed to set global credentials: {e}"))
        raise click.Abort() from None


@credential_commands.command("list")
@common_options
@click.pass_context
@async_command
async def list_credentials(ctx: click.Context) -> None:
    """List devices with stored credentials."""
    console = ctx.obj.console
    container = ctx.obj.container
    repo = container.get_credentials_repository()

    try:
        creds = await repo.list_all()
        if not creds:
            console.print(Messages.warning("No credentials stored."))
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("MAC Address", style="cyan")
        table.add_column("Username", style="green")
        table.add_column("Last Seen IP", style="yellow")

        for c in creds:
            mac_display = c.mac
            if c.mac == "*":
                mac_display = "[bold]GLOBAL FALLBACK[/bold]"
            table.add_row(mac_display, c.username, c.last_seen_ip or "-")

        console.print(table)
    except Exception as e:
        console.print(Messages.error(f"Failed to list credentials: {e}"))


@credential_commands.command("delete")
@click.argument("mac")
@common_options
@click.pass_context
@async_command
async def delete_credential(ctx: click.Context, mac: str) -> None:
    """Delete credentials for a device."""
    console = ctx.obj.console
    container = ctx.obj.container
    repo = container.get_credentials_repository()

    try:
        await repo.delete(mac)
        console.print(f"✅ Credentials deleted for [bold]{mac.upper()}[/bold]")
    except Exception as e:
        console.print(Messages.error(f"Failed to delete credentials: {e}"))
        raise click.Abort() from None
