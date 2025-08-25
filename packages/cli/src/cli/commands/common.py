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
        "--from-config", is_flag=True, help="Use devices from configuration file"
    )
    @click.option(
        "--devices",
        multiple=True,
        callback=validate_ip_address,
        help="Specific device IPs (can be used multiple times)",
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


def parse_ip_range(ip_range: str) -> tuple[str, str]:
    """
    Parse IP range string into start and end IPs.

    Supports formats:
    - 192.168.1.1-192.168.1.50
    - 192.168.1.1/24
    - 192.168.1.1 (single IP)
    """
    if "-" in ip_range:
        parts = ip_range.split("-", 1)
        if len(parts) != 2:
            raise ValueError("Invalid range format. Use: start_ip-end_ip")
        start_ip, end_ip = parts[0].strip(), parts[1].strip()

        try:
            ipaddress.ip_address(start_ip)
            ipaddress.ip_address(end_ip)
        except ValueError as e:
            raise ValueError(f"Invalid IP address in range: {e}") from e

        return start_ip, end_ip

    elif "/" in ip_range:
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
            hosts = list(network.hosts())
            if hosts:
                return str(hosts[0]), str(hosts[-1])
            else:
                return str(network.network_address), str(network.network_address)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation: {e}") from e

    else:
        try:
            ipaddress.ip_address(ip_range)
            return ip_range, ip_range
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {e}") from e


def validate_ip_address(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if value is None:
        return value

    if isinstance(value, list | tuple):
        validated = []
        for ip in value:
            try:
                ipaddress.ip_address(ip)
                validated.append(ip)
            except ValueError as e:
                raise click.BadParameter(f"'{ip}' is not a valid IP address") from e
        return tuple(validated)
    else:
        try:
            ipaddress.ip_address(value)
            return value
        except ValueError as e:
            raise click.BadParameter(f"'{value}' is not a valid IP address") from e


def validate_ip_range(ctx: click.Context, param: click.Parameter, value: Any) -> Any:
    if not value:
        return value

    if isinstance(value, list | tuple):
        validated: list[str] = []
        for ip_range in value:
            try:
                parse_ip_range(ip_range)
                validated.append(ip_range)
            except Exception as e:
                raise click.BadParameter(
                    f"'{ip_range}' is not a valid IP range: {e}"
                ) from e
        return tuple(validated)
    else:
        try:
            parse_ip_range(value)
            return value
        except Exception as e:
            raise click.BadParameter(f"'{value}' is not a valid IP range: {e}") from e


def create_scan_request(
    ip_ranges: list[str],
    devices: list[str],
    from_config: bool,
    timeout: float,
    workers: int,
    use_mdns: bool = False,
) -> ScanRequest:

    if use_mdns:
        return ScanRequest(
            use_predefined=False,
            start_ip=None,
            end_ip=None,
            timeout=timeout,
            max_workers=workers,
            use_mdns=use_mdns,
        )

    if from_config:
        return ScanRequest(
            use_predefined=True,
            start_ip=None,
            end_ip=None,
            timeout=timeout,
            max_workers=workers,
            use_mdns=use_mdns,
        )

    if ip_ranges:
        start_ip, end_ip = parse_ip_range(ip_ranges[0])
        return ScanRequest(
            start_ip=start_ip,
            end_ip=end_ip,
            use_predefined=False,
            timeout=timeout,
            max_workers=workers,
            use_mdns=use_mdns,
        )

    if devices:
        if len(devices) == 1:
            start_ip, end_ip = parse_ip_range(devices[0])
        else:
            start_ip, end_ip = devices[0], devices[-1]

        return ScanRequest(
            start_ip=start_ip,
            end_ip=end_ip,
            use_predefined=False,
            timeout=timeout,
            max_workers=workers,
        )

    return ScanRequest(
        use_predefined=True,
        start_ip=None,
        end_ip=None,
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
