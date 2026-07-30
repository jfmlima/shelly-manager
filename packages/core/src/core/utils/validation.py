"""
Shared validation utilities for the core domain.
"""

import ipaddress
import re


def normalize_mac(mac: str) -> str:
    """
    Normalize a MAC address to uppercase without separators.

    Args:
        mac: MAC address in any format (with or without colons/dashes)

    Returns:
        Normalized MAC address (uppercase, no separators)

    Examples:
        >>> normalize_mac("aa:bb:cc:dd:ee:ff")
        'AABBCCDDEEFF'
        >>> normalize_mac("AA-BB-CC-DD-EE-FF")
        'AABBCCDDEEFF'
        >>> normalize_mac("AABBCCDDEEFF")
        'AABBCCDDEEFF'
    """
    return mac.upper().replace(":", "").replace("-", "")


def is_valid_mac(mac: str) -> bool:
    """
    Check if a string is a valid MAC address.

    Args:
        mac: MAC address to validate (any format)

    Returns:
        True if valid MAC address, False otherwise
    """
    if mac == "*":  # Special case for global fallback
        return True
    mac_clean = normalize_mac(mac)
    return bool(re.match(r"^[0-9A-F]{12}$", mac_clean))


def validate_mac(mac: str, allow_wildcard: bool = False) -> str:
    """
    Normalize a MAC address, raising when it is invalid.

    Args:
        mac: MAC address in any format
        allow_wildcard: Accept "*" (the global credentials fallback) as-is

    Returns:
        Normalized MAC address (uppercase, no separators)

    Raises:
        ValueError: If the MAC address is invalid
    """
    if mac == "*" and allow_wildcard:
        return mac
    if mac == "*" or not is_valid_mac(mac):
        raise ValueError(
            "Invalid MAC address format. Expected AA:BB:CC:DD:EE:FF or AABBCCDDEEFF"
        )
    return normalize_mac(mac)


def validate_ip_address(ip: str) -> str:
    """
    Validate an IPv4 address string.

    Args:
        ip: The IP address string to validate

    Returns:
        The validated IP address string

    Raises:
        ValueError: If the IP address is invalid
    """
    try:
        ipaddress.IPv4Address(ip)
    except ipaddress.AddressValueError as e:
        raise ValueError(f"Invalid IP address: {ip}") from e
    return ip


def validate_ip_address_list(ips: list[str]) -> list[str]:
    """
    Validate a list of IPv4 address strings.

    Args:
        ips: The list of IP address strings to validate

    Returns:
        The validated list of IP address strings

    Raises:
        ValueError: If any IP address in the list is invalid
    """
    for ip in ips:
        validate_ip_address(ip)
    return ips
