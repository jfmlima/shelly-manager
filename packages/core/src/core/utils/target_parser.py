"""
Target parsing utilities for IP addresses, ranges, and CIDR notation.
"""

import ipaddress
from collections.abc import Iterator


def parse_target(target: str) -> Iterator[str]:
    """
    Parse a target string and yield individual IPs.

    Supports:
    - Single IP: "192.168.1.1"
    - IP range: "192.168.1.1-192.168.1.254" or "192.168.1.1-254"
    - CIDR notation: "192.168.1.0/24"

    Args:
        target: Target string to parse

    Yields:
        Individual IP addresses

    Raises:
        ValueError: If target format is invalid
    """
    target = target.strip()

    if not target:
        raise ValueError("Empty target string")

    # CIDR notation
    if "/" in target:
        try:
            network = ipaddress.ip_network(target, strict=False)
            # For /31 and /32, include all addresses
            if network.num_addresses <= 2:
                for ip in network:
                    yield str(ip)
            else:
                # Exclude network and broadcast for larger subnets
                for ip in network.hosts():
                    yield str(ip)
            return
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation '{target}': {e}") from e

    # IP range
    if "-" in target:
        parts = target.split("-", 1)
        start_str = parts[0].strip()
        end_str = parts[1].strip()

        try:
            start_ip = ipaddress.IPv4Address(start_str)

            # Handle short form: "192.168.1.1-254" → "192.168.1.1-192.168.1.254"
            if "." not in end_str:
                # end_str is just the last octet
                start_parts = start_str.split(".")
                end_str = ".".join(start_parts[:3]) + "." + end_str

            end_ip = ipaddress.IPv4Address(end_str)

            if start_ip > end_ip:
                raise ValueError(f"Start IP {start_ip} is greater than end IP {end_ip}")

            current = int(start_ip)
            end = int(end_ip)

            while current <= end:
                yield str(ipaddress.IPv4Address(current))
                current += 1
            return

        except ValueError as e:
            raise ValueError(f"Invalid IP range '{target}': {e}") from e

    # Single IP
    try:
        ipaddress.IPv4Address(target)
        yield target
    except ValueError as e:
        raise ValueError(f"Invalid IP address '{target}': {e}") from e


def expand_targets(targets: list[str]) -> list[str]:
    """
    Expand all targets into individual IP addresses.

    Args:
        targets: List of target strings (IPs, ranges, CIDR)

    Returns:
        List of individual IP addresses

    Raises:
        ValueError: If any target format is invalid
    """
    result: list[str] = []
    for target in targets:
        result.extend(parse_target(target))
    return result


def validate_target(target: str) -> None:
    """
    Validate a target string without expanding it.

    Args:
        target: Target string to validate

    Raises:
        ValueError: If target format is invalid
    """
    # Just try to parse it, don't yield results
    list(parse_target(target))


__all__ = ["parse_target", "expand_targets", "validate_target"]
