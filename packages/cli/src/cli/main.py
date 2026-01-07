"""
Main Click-based CLI for Shelly Manager.
"""

import sys

import click
from rich.console import Console

from .commands import (
    bulk_commands,
    device_commands,
    export_commands,
)
from .commands.device_commands import scan
from .credential_commands import credential_commands
from .dependencies.container import CLIContainer


class CliContext:

    def __init__(self) -> None:
        self.console = Console()
        self.container = CLIContainer()
        self.verbose = False


@click.group(invoke_without_command=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, version: bool) -> None:
    """
    🏠 Shelly Manager - Smart home device management tool.

    Manage Shelly devices on your network with powerful scanning,
    configuration, and update capabilities. Zero configuration required.

    Examples:
      shelly-manager scan 192.168.1.0/24
      shelly-manager device status -t 192.168.1.100
      shelly-manager device update -t 192.168.1.100
      shelly-manager bulk reboot 192.168.1.0/24
    """
    cli_ctx = CliContext()
    cli_ctx.verbose = verbose

    ctx.ensure_object(dict)
    ctx.obj = cli_ctx

    if version:
        cli_ctx.console.print("[bold blue]Shelly Manager CLI[/bold blue]")
        cli_ctx.console.print("Version: 1.0.0")
        cli_ctx.console.print("Built with ❤️ for smart home automation")
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        cli_ctx.console.print(ctx.get_help())


cli.add_command(bulk_commands, name="bulk")
cli.add_command(device_commands, name="device")
cli.add_command(export_commands, name="export")
cli.add_command(credential_commands, name="credentials")

cli.add_command(scan)


if __name__ == "__main__":
    cli()
