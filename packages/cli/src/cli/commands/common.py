"""
Common Click utilities, decorators, and options.
"""

import asyncio
import ipaddress
from collections.abc import Callable
from functools import wraps
from typing import Any

import click
from core.domain.value_objects.scan_request import ScanRequest
from rich.console import Console
from rich.table import Table

from ..presentation.styles import format_device_status


def common_options(func: Callable) -> Callable:

    @click.option(
        "--timeout", type=float, default=3.0, help="Request timeout in seconds"
    )
    @click.option("--workers", type=int, default=50, help="Maximum concurrent workers")
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


def device_targeting_options(func: Callable) -> Callable:

    @click.option(
        "--target",
        "-t",
        "targets_opt",
        multiple=True,
        help="Specific device IPs, ranges, or CIDR (can be used multiple times)",
    )
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper


def async_command(func: Callable) -> Callable:
    """Decorator to run async functions in Click commands."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def parse_ip_list(ip_list_str: str) -> list[str]:
    """
    Parse comma-separated IP list.

    Args:
        ip_list_str: Comma-separated IP addresses

    Returns:
        List of IP addresses
    """

    if not ip_list_str:
        return []

    ips = []
    for ip in ip_list_str.split(","):
        ip = ip.strip()
        if ip:
            try:
                ipaddress.ip_address(ip)
                ips.append(ip)
            except ValueError as e:
                raise click.BadParameter(f"'{ip}' is not a valid IP address") from e

    return ips


def create_scan_request(
    targets: list[str],
    timeout: float,
    workers: int,
    use_mdns: bool = False,
) -> ScanRequest:
    """Create a ScanRequest from CLI arguments."""

    if not use_mdns and not targets:
        raise click.BadParameter(
            "At least one target is required when not using mDNS. "
            "Use --target or --use-mdns."
        )

    return ScanRequest(
        targets=targets,
        use_mdns=use_mdns,
        timeout=timeout,
        max_workers=workers,
    )


def format_device_table(devices: list[Any], console: Console) -> None:
    if not devices:
        return

    table = Table(title="Shelly Devices")
    table.add_column("IP Address", style="cyan")
    table.add_column("Device Type", style="green")
    table.add_column("Name", style="blue")
    table.add_column("Firmware", style="magenta")
    table.add_column("Status", style="yellow")

    for device in devices:
        if hasattr(device, "ip"):
            ip = device.ip
            device_type = getattr(device, "device_type", "Unknown")
            name = getattr(device, "device_name", "Unknown")
            firmware = getattr(device, "firmware_version", "Unknown")
            status = getattr(device, "status", "Unknown")
        else:
            ip = device.get("ip", "Unknown")
            device_type = device.get("device_type", "Unknown")
            name = device.get("device_name", "Unknown")
            firmware = device.get("firmware_version", "Unknown")
            status = device.get("status", "Unknown")

        table.add_row(ip, device_type, name, firmware, format_device_status(status))

    console.print(table)


def confirm_action(message: str, default: bool = False) -> bool:
    return click.confirm(message, default=default)
