"""
Device-related entities for CLI operations.
"""

from typing import Any

from pydantic import BaseModel, Field

from .common import OperationResult


class DeviceScanRequest(BaseModel):
    """Request for scanning devices."""

    ip_ranges: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    devices: list[str] = Field(default_factory=list)
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=50, gt=0, le=200)
    task_description: str = Field(
        default="Scanning for devices...",
        description="Description shown in progress bar",
    )


class DeviceStatusRequest(BaseModel):
    """Request for checking device status."""

    devices: list[str] = Field(
        default_factory=list, description="List of device IP addresses to check"
    )
    from_config: bool = Field(
        default=False, description="Whether to get devices from configuration"
    )
    include_updates: bool = Field(
        default=True, description="Whether to include firmware update information"
    )
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=50, gt=0, le=200)
    verbose: bool = Field(
        default=False, description="Whether to show verbose error messages"
    )


class DeviceRebootRequest(BaseModel):
    """Request for rebooting devices."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    force: bool = Field(default=False, description="Skip confirmation prompt")
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=50, gt=0, le=200)


class DeviceRebootResult(OperationResult):
    """Result of a device reboot operation."""

    reboot_initiated: bool = Field(
        default=False, description="Whether the reboot was successfully initiated"
    )


class DeviceStatusResult(OperationResult):
    """Result of a device status check."""

    firmware_version: str | None = Field(default=None)
    device_type: str | None = Field(default=None)
    device_name: str | None = Field(default=None)
    update_available: bool = Field(default=False)
    new_firmware_version: str | None = Field(default=None)


class DeviceConfigUpdateRequest(BaseModel):
    """Request for updating device configuration."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    config_file: str | None = Field(
        default=None, description="Configuration file to apply to devices"
    )
    force: bool = Field(default=False, description="Skip confirmation prompt")
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)


class DeviceConfigUpdateResult(OperationResult):
    """Result of a device configuration update operation."""

    config_applied: bool = Field(
        default=False, description="Whether the configuration was successfully applied"
    )
    config_data: dict[str, Any] | None = Field(default=None)


class DeviceFirmwareUpdateRequest(BaseModel):
    """Request for firmware update operation."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    channel: str = Field(
        default="stable", description="Update channel (stable or beta)"
    )
    force: bool = Field(default=False, description="Skip all confirmation prompts")
    check_only: bool = Field(
        default=False, description="Only check for updates, do not install"
    )
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)


class DeviceFirmwareUpdateResult(OperationResult):
    """Result of a firmware update operation."""

    current_version: str | None = Field(default=None)
    new_version: str | None = Field(default=None)
    update_available: bool = Field(default=False)
    update_initiated: bool = Field(
        default=False, description="Whether the update was successfully initiated"
    )
    time_taken_seconds: float | None = Field(default=None)
