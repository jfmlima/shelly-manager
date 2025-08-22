"""
Request models for API validation.
"""

import ipaddress
from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class ScanDevicesRequest(BaseModel):

    start_ip: str | None = Field(None, description="Starting IP address for range scan")
    end_ip: str | None = Field(None, description="Ending IP address for range scan")
    use_predefined: bool = Field(
        True, description="Use predefined IPs from configuration"
    )
    timeout: float = Field(
        3.0, ge=0.1, le=30.0, description="Timeout for each device scan"
    )
    max_workers: int = Field(50, ge=1, le=200, description="Maximum concurrent workers")

    @field_validator("start_ip", "end_ip")
    @classmethod
    def validate_ip(cls, v: str | None) -> str | None:
        if v is not None:
            _validate_ip_address(v)
        return v

    @field_validator("end_ip")
    @classmethod
    def validate_ip_range(cls, v: str | None, info: ValidationInfo) -> str | None:
        if (
            v is not None
            and "start_ip" in info.data
            and info.data["start_ip"] is not None
        ):
            start = ipaddress.IPv4Address(info.data["start_ip"])
            end = ipaddress.IPv4Address(v)
            if start > end:
                raise ValueError("start_ip must be less than or equal to end_ip")
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
