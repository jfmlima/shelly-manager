"""
Request models for API validation.
"""

from typing import Any

from core.domain.entities.backup_schedule import EVERY_PRESETS, MIN_INTERVAL_SECONDS
from core.domain.entities.config_snapshot import (
    CONFIGURABLE_COMPONENT_TYPES,
    EXPORTABLE_COMPONENT_TYPES,
)
from core.utils.validation import (
    validate_ip_address,
    validate_ip_address_list,
    validate_mac,
)
from pydantic import BaseModel, Field, field_validator, model_validator


class CredentialCreateRequest(BaseModel):
    """Request model for creating or updating device credentials."""

    mac: str = Field(..., description="Device MAC address or '*' for global")
    username: str = Field(default="admin")
    password: str = Field(..., min_length=1)

    @field_validator("mac")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        """Validate and normalize MAC address."""
        return validate_mac(v, allow_wildcard=True)


class AddIPRequest(BaseModel):
    ip: str = Field(..., description="IP address to add")

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        return validate_ip_address(v)


class RemoveIPRequest(BaseModel):
    ip: str = Field(..., description="IP address to remove")

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        return validate_ip_address(v)


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
        return validate_ip_address_list(v)

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
        return validate_ip_address_list(v)

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


class CreateProvisioningProfileRequest(BaseModel):
    """Request model for creating a provisioning profile."""

    name: str = Field(..., min_length=1, max_length=100)
    wifi_ssid: str | None = Field(None, max_length=32)
    wifi_password: str | None = Field(None)
    mqtt_enabled: bool = Field(default=False)
    mqtt_server: str | None = Field(None)
    mqtt_user: str | None = Field(None)
    mqtt_password: str | None = Field(None)
    mqtt_topic_prefix_template: str | None = Field(None, max_length=300)
    auth_password: str | None = Field(None)
    device_name_template: str | None = Field(None, max_length=100)
    timezone: str | None = Field(None)
    cloud_enabled: bool = Field(default=False)
    is_default: bool = Field(default=False)


class UpdateProvisioningProfileRequest(BaseModel):
    """Request model for updating a provisioning profile."""

    name: str | None = Field(None, min_length=1, max_length=100)
    wifi_ssid: str | None = Field(None, max_length=32)
    wifi_password: str | None = Field(None)
    mqtt_enabled: bool | None = Field(None)
    mqtt_server: str | None = Field(None)
    mqtt_user: str | None = Field(None)
    mqtt_password: str | None = Field(None)
    mqtt_topic_prefix_template: str | None = Field(None, max_length=300)
    auth_password: str | None = Field(None)
    device_name_template: str | None = Field(None, max_length=100)
    timezone: str | None = Field(None)
    cloud_enabled: bool | None = Field(None)
    is_default: bool | None = Field(None)


class ProvisionDeviceAPIRequest(BaseModel):
    """Request model for provisioning a device."""

    device_ip: str = Field(
        default="192.168.33.1",
        description="IP address of the device in AP mode",
    )
    profile_id: int | None = Field(
        default=None,
        description="Profile ID to use. None uses the default profile.",
    )
    timeout: float = Field(default=10.0, ge=1.0, le=60.0)

    @field_validator("device_ip")
    @classmethod
    def validate_device_ip(cls, v: str) -> str:
        return validate_ip_address(v)


class DetectDeviceAPIRequest(BaseModel):
    """Request model for detecting a device at AP IP."""

    device_ip: str = Field(
        default="192.168.33.1",
        description="IP address of the device in AP mode",
    )
    timeout: float = Field(default=5.0, ge=1.0, le=30.0)

    @field_validator("device_ip")
    @classmethod
    def validate_device_ip(cls, v: str) -> str:
        return validate_ip_address(v)


class VerifyProvisionRequest(BaseModel):
    """Request model for verifying a provisioned device on the target network."""

    device_mac: str = Field(..., description="MAC address of the provisioned device")
    scan_targets: list[str] = Field(
        ...,
        min_length=1,
        description="Network targets to scan for the device",
    )
    timeout: float = Field(default=30.0, ge=5.0, le=120.0)


class CreateBackupRequest(BaseModel):
    """Request model for capturing a device configuration backup."""

    device_ip: str = Field(..., description="Target device IP address")
    name: str | None = Field(default=None, description="Optional backup label")

    @field_validator("device_ip")
    @classmethod
    def validate_device_ip(cls, v: str) -> str:
        return validate_ip_address(v)


class CreateBackupScheduleRequest(BaseModel):
    """Request model for creating a backup schedule.

    Cadence is set with exactly one of ``every`` (a preset) or ``interval_seconds``.
    """

    name: str = Field(..., min_length=1, max_length=100)
    target_ips: list[str] = Field(default_factory=list)
    target_macs: list[str] = Field(default_factory=list)
    all_credentialed: bool = Field(default=False)
    every: str | None = Field(
        default=None, description="Preset cadence: hourly, daily, or weekly"
    )
    interval_seconds: int | None = Field(default=None, ge=MIN_INTERVAL_SECONDS)
    enabled: bool = Field(default=True)
    retention_keep_last: int | None = Field(default=None, ge=1)
    retention_max_age_days: int | None = Field(default=None, ge=1)

    @field_validator("target_ips")
    @classmethod
    def validate_target_ips(cls, v: list[str]) -> list[str]:
        return _validate_targets(v)

    @field_validator("target_macs")
    @classmethod
    def validate_target_macs(cls, v: list[str]) -> list[str]:
        return _normalize_macs(v)

    @field_validator("every")
    @classmethod
    def validate_every(cls, v: str | None) -> str | None:
        if v is not None and v not in EVERY_PRESETS:
            raise ValueError(
                f"Invalid cadence '{v}'. Must be one of: {sorted(EVERY_PRESETS)}"
            )
        return v

    @model_validator(mode="after")
    def validate_cadence(self) -> "CreateBackupScheduleRequest":
        if (self.every is None) == (self.interval_seconds is None):
            raise ValueError("Provide exactly one of 'every' or 'interval_seconds'")
        return self

    def resolved_interval_seconds(self) -> int:
        if self.every is not None:
            return EVERY_PRESETS[self.every]
        assert self.interval_seconds is not None  # guaranteed by the validator
        return self.interval_seconds


class UpdateBackupScheduleRequest(BaseModel):
    """Request model for partially updating a backup schedule."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    target_ips: list[str] | None = Field(default=None)
    target_macs: list[str] | None = Field(default=None)
    all_credentialed: bool | None = Field(default=None)
    every: str | None = Field(default=None)
    interval_seconds: int | None = Field(default=None, ge=MIN_INTERVAL_SECONDS)
    enabled: bool | None = Field(default=None)
    retention_keep_last: int | None = Field(default=None, ge=1)
    retention_max_age_days: int | None = Field(default=None, ge=1)

    @field_validator("target_ips")
    @classmethod
    def validate_target_ips(cls, v: list[str] | None) -> list[str] | None:
        return _validate_targets(v) if v is not None else None

    @field_validator("target_macs")
    @classmethod
    def validate_target_macs(cls, v: list[str] | None) -> list[str] | None:
        return _normalize_macs(v) if v is not None else None

    @field_validator("every")
    @classmethod
    def validate_every(cls, v: str | None) -> str | None:
        if v is not None and v not in EVERY_PRESETS:
            raise ValueError(
                f"Invalid cadence '{v}'. Must be one of: {sorted(EVERY_PRESETS)}"
            )
        return v

    @model_validator(mode="after")
    def validate_cadence(self) -> "UpdateBackupScheduleRequest":
        if self.every is not None and self.interval_seconds is not None:
            raise ValueError("Provide at most one of 'every' or 'interval_seconds'")
        return self

    def resolved_interval_seconds(self) -> int | None:
        if self.every is not None:
            return EVERY_PRESETS[self.every]
        return self.interval_seconds


class RestoreBackupRequest(BaseModel):
    """Request model for restoring a backup onto a device."""

    device_ip: str = Field(..., description="Target device IP address")
    component_keys: list[str] | None = Field(
        default=None,
        description=(
            "Component keys to restore. When omitted, restores all components "
            "except network types (wifi/eth/mqtt/ws/cloud)."
        ),
    )
    allow_mac_mismatch: bool = Field(
        default=False, description="Restore even if the target MAC differs"
    )
    reboot: bool = Field(
        default=False, description="Reboot the device after a successful restore"
    )

    @field_validator("device_ip")
    @classmethod
    def validate_device_ip(cls, v: str) -> str:
        return validate_ip_address(v)


def _validate_targets(targets: list[str]) -> list[str]:
    """Validate IP / range / CIDR target strings without expanding them."""
    from core.utils.target_parser import validate_target

    for target in targets:
        try:
            validate_target(target)
        except ValueError as e:
            raise ValueError(f"Invalid target '{target}': {e}") from e
    return targets


def _normalize_macs(macs: list[str]) -> list[str]:
    return [validate_mac(mac) for mac in macs]


def _validate_component_type(component_type: str) -> str:
    if component_type not in CONFIGURABLE_COMPONENT_TYPES:
        raise ValueError(f"Invalid component type: {component_type}")
    return component_type


def _validate_component_types(component_types: list[str]) -> list[str]:
    invalid_types = [
        comp for comp in component_types if comp not in EXPORTABLE_COMPONENT_TYPES
    ]
    if invalid_types:
        raise ValueError(f"Invalid component types: {invalid_types}")
    return component_types
