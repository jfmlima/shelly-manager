"""
BulkActionRequest domain model.
"""

import ipaddress
from typing import Any

from pydantic import BaseModel, Field, field_validator


class BulkActionRequest(BaseModel):

    action_type: str = Field(..., description="Type of action to perform")
    device_ips: list[str] = Field(
        ..., min_length=1, description="List of device IP addresses"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        valid_bulk_actions = ["update", "reboot", "config-set"]
        if v not in valid_bulk_actions:
            raise ValueError(
                f"Invalid bulk action type. Must be one of: {valid_bulk_actions}"
            )
        return v

    @field_validator("device_ips")
    @classmethod
    def validate_ip_addresses(cls, v: list[str]) -> list[str]:
        for ip in v:
            try:
                ipaddress.IPv4Address(ip)
            except ipaddress.AddressValueError as e:
                raise ValueError(f"Invalid IP address: {ip}") from e
        return v
