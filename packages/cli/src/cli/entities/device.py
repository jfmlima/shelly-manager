"""
Device-related entities for CLI operations.
"""

from pydantic import BaseModel, Field

from .common import OperationResult


class DeviceScanRequest(BaseModel):
    """Request for scanning devices."""

    ip_ranges: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    devices: list[str] = Field(default_factory=list)
    use_mdns: bool = Field(default=False)
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


class DeviceStatusResult(OperationResult):
    """Result of a device status check."""

    firmware_version: str | None = Field(default=None)
    device_type: str | None = Field(default=None)
    device_name: str | None = Field(default=None)
    update_available: bool = Field(default=False)
    new_firmware_version: str | None = Field(default=None)
