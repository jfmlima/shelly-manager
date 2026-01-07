"""
Request models for API validation.
"""

import ipaddress
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CredentialCreateRequest(BaseModel):
    """Request model for creating or updating device credentials."""

    mac: str = Field(..., description="Device MAC address or '*' for global")
    username: str = Field(default="admin")
    password: str = Field(..., min_length=1)

    @field_validator("mac")
    @classmethod
    def validate_mac(cls, v: str) -> str:
        """Validate and normalize MAC address."""
        if v == "*":
            return v
        mac_clean = v.upper().replace(":", "").replace("-", "")
        if not re.match(r"^[0-9A-F]{12}$", mac_clean):
            raise ValueError(
                "Invalid MAC address format. Expected format: AA:BB:CC:DD:EE:FF or AABBCCDDEEFF"
            )
        return mac_clean  # Return normalized form (uppercase, no separators)


class ScanDevicesRequest(BaseModel):
    targets: list[str] = Field(
        default_factory=list,
        description="IP targets: individual IPs ('192.168.1.1'), ranges ('192.168.1.1-254'), or CIDR ('192.168.1.0/24')",
    )
    use_mdns: bool = Field(
        False,
        description="Use mDNS to discover devices (ignores targets)",
    )
    timeout: float = Field(
        3.0,
        ge=0.1,
        le=30.0,
        description="Timeout for each device scan",
    )
    max_workers: int = Field(
        50,
        ge=1,
        le=200,
        description="Maximum concurrent workers",
    )

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: list[str]) -> list[str]:
        if not v:
            return v

        from core.utils.target_parser import validate_target

        for target in v:
            try:
                validate_target(target)
            except ValueError as e:
                raise ValueError(f"Invalid target '{target}': {str(e)}") from e

        return v


class DeviceActionRequest(BaseModel):

    action_type: str = Field(..., description="Type of action to perform")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, v: str) -> str:
        valid_actions = [
            "list",
            "update",
            "reboot",
            "config-get",
            "config-set",
            "status",
        ]
        if v not in valid_actions:
            raise ValueError(f"Invalid action type. Must be one of: {valid_actions}")
        return v


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
        valid_actions = ["update", "reboot", "config-set"]
        if v not in valid_actions:
            raise ValueError(
                f"Invalid bulk action type. Must be one of: {valid_actions}"
            )
        return v

    @field_validator("device_ips")
    @classmethod
    def validate_ips(cls, v: list[str]) -> list[str]:
        return _validate_ip_addresses(v)


class UpdateConfigRequest(BaseModel):

    predefined_ips: list[str] | None = Field(
        None, description="List of predefined IP addresses"
    )
    scan_settings: dict[str, Any] | None = Field(None, description="Scan configuration")
    export_settings: dict[str, Any] | None = Field(
        None, description="Export configuration"
    )
    default_credentials: dict[str, str] | None = Field(
        None, description="Default device credentials"
    )

    @field_validator("predefined_ips")
    @classmethod
    def validate_predefined_ips(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            _validate_ip_addresses(v)
        return v


class AddIPRequest(BaseModel):

    ip: str = Field(..., description="IP address to add")

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        return _validate_ip_address(v)


class RemoveIPRequest(BaseModel):

    ip: str = Field(..., description="IP address to remove")

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        return _validate_ip_address(v)


class UpdateDeviceConfigRequest(BaseModel):

    config: dict[str, Any] = Field(..., description="Device configuration object")


class BulkExportConfigRequest(BaseModel):
    """Request for bulk configuration export."""

    device_ips: list[str] = Field(
        ..., min_length=1, description="List of device IP addresses"
    )
    component_types: list[str] = Field(
        ..., min_length=1, description="List of component types to export"
    )

    @field_validator("device_ips")
    @classmethod
    def validate_device_ips(cls, v: list[str]) -> list[str]:
        return _validate_ip_addresses(v)

    @field_validator("component_types")
    @classmethod
    def validate_component_types(cls, v: list[str]) -> list[str]:
        return _validate_component_types(v)


class BulkApplyConfigRequest(BaseModel):
    """Request for bulk configuration apply."""

    device_ips: list[str] = Field(
        ..., min_length=1, description="List of device IP addresses"
    )
    component_type: str = Field(
        ..., description="Single component type to apply configuration to"
    )
    config: dict[str, Any] = Field(..., description="Configuration object to apply")

    @field_validator("device_ips")
    @classmethod
    def validate_device_ips(cls, v: list[str]) -> list[str]:
        return _validate_ip_addresses(v)

    @field_validator("component_type")
    @classmethod
    def validate_component_type(cls, v: str) -> str:
        return _validate_component_type(v)

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("Configuration cannot be empty")
        return v


def _validate_ip_address(ip: str) -> str:
    try:
        ipaddress.IPv4Address(ip)
    except ipaddress.AddressValueError as e:
        raise ValueError(f"Invalid IP address: {ip}") from e
    return ip


def _validate_ip_addresses(ips: list[str]) -> list[str]:
    for ip in ips:
        _validate_ip_address(ip)
    return ips


def _get_valid_component_types() -> list[str]:
    return [
        "switch",
        "input",
        "cover",
        "sys",
        "cloud",
        "wifi",
        "ble",
        "mqtt",
        "ws",
        "script",
        "knx",
        "modbus",
        "zigbee",
        "button",
        "text",
        "number",
        "group",
        "enum",
        "boolean",
    ]


def _validate_component_type(component_type: str) -> str:
    valid_components = _get_valid_component_types()
    if component_type not in valid_components:
        raise ValueError(f"Invalid component type: {component_type}")
    return component_type


def _validate_component_types(component_types: list[str]) -> list[str]:
    valid_components = _get_valid_component_types()
    invalid_types = [comp for comp in component_types if comp not in valid_components]
    if invalid_types:
        raise ValueError(f"Invalid component types: {invalid_types}")
    return component_types
