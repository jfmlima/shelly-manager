"""
Shared validation utilities for the core domain.
"""

import ipaddress
from typing import Any

from pydantic import field_validator


def validate_ip_address(cls: Any, v: str) -> str:
    """
    Reusable IP address validator for Pydantic models.

    Args:
        cls: The Pydantic model class (automatically passed by field_validator)
        v: The IP address string to validate

    Returns:
        The validated IP address string

    Raises:
        ValueError: If the IP address is invalid
    """
    try:
        ipaddress.IPv4Address(v)
    except ipaddress.AddressValueError as e:
        raise ValueError(f"Invalid IP address: {v}") from e
    return v


def validate_ip_address_list(cls: Any, v: list[str]) -> list[str]:
    """
    Reusable IP address list validator for Pydantic models.

    Args:
        cls: The Pydantic model class (automatically passed by field_validator)
        v: The list of IP address strings to validate

    Returns:
        The validated list of IP address strings

    Raises:
        ValueError: If any IP address in the list is invalid
    """
    for ip in v:
        try:
            ipaddress.IPv4Address(ip)
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid IP address: {ip}") from e
    return v


ip_validator = field_validator("device_ip", "ip")(validate_ip_address)
ip_list_validator = field_validator("device_ips", "ips")(validate_ip_address_list)
