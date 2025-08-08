"""
Main Click-based CLI for Shelly Manager.
"""

import sys

import click
from rich.console import Console

from .commands import (
    device_commands,
    export_commands,
)
from .commands.device_commands import scan
from .dependencies.container import CLIContainer


class CliContext:

    def __init__(self) -> None:
        self.console = Console()
        self.container = CLIContainer()
        self.verbose = False
        self.config_file: str | None = None


@click.group(invoke_without_command=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--config", type=click.Path(exists=True), help="Path to configuration file"
)
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, config: str | None, version: bool) -> None:
    """
    🏠 Shelly Manager - Smart home device management tool.

    Manage Shelly devices on your network with powerful scanning,
    configuration, and update capabilities.

    Examples:
      shelly-manager scan
      shelly-manager device status 192.168.1.100
      shelly-manager device update firmware --all
      shelly-manager device update config --from-config
    """
    cli_ctx = CliContext()
    cli_ctx.verbose = verbose
    cli_ctx.config_file = config

    ctx.ensure_object(dict)
    ctx.obj = cli_ctx

    if version:
        cli_ctx.console.print("[bold blue]Shelly Manager CLI[/bold blue]")
        cli_ctx.console.print("Version: 1.0.0")
        cli_ctx.console.print("Built with ❤️ for smart home automation")
        sys.exit(0)

    if config:
        cli_ctx.container = CLIContainer(config_file_path=config)

    if ctx.invoked_subcommand is None:
        cli_ctx.console.print(ctx.get_help())


cli.add_command(device_commands, name="device")
cli.add_command(export_commands, name="export")

cli.add_command(scan)


if __name__ == "__main__":
    cli()
