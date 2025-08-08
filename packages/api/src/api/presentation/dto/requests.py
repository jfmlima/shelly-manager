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
            try:
                ipaddress.IPv4Address(v)
            except ipaddress.AddressValueError as e:
                raise ValueError(f"Invalid IP address: {v}") from e
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
        for ip in v:
            try:
                ipaddress.IPv4Address(ip)
            except ipaddress.AddressValueError as e:
                raise ValueError(f"Invalid IP address: {ip}") from e
        return v


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
            for ip in v:
                try:
                    ipaddress.IPv4Address(ip)
                except ipaddress.AddressValueError as e:
                    raise ValueError(f"Invalid IP address: {ip}") from e
        return v


class AddIPRequest(BaseModel):

    ip: str = Field(..., description="IP address to add")

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.IPv4Address(v)
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid IP address: {v}") from e
        return v


class RemoveIPRequest(BaseModel):

    ip: str = Field(..., description="IP address to remove")

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.IPv4Address(v)
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid IP address: {v}") from e
        return v


class UpdateDeviceConfigRequest(BaseModel):

    config: dict[str, Any] = Field(..., description="Device configuration object")
