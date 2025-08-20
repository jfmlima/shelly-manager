"""
Update-related entities for CLI operations.
"""

from pydantic import BaseModel, Field

from .common import OperationResult


class DeviceUpdateRequest(BaseModel):
    """Request for updating a single device."""

    device: str = Field(description="IP address of the device to update")
    beta: bool = Field(default=False, description="Whether to update to beta firmware")
    force: bool = Field(default=False, description="Skip pre-update checks")
    skip_backup: bool = Field(
        default=False, description="Skip configuration backup before update"
    )
    timeout: float = Field(default=3.0, gt=0)


class BulkUpdateRequest(BaseModel):
    """Request for bulk updating devices."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    beta: bool = Field(default=False, description="Whether to update to beta firmware")
    force: bool = Field(default=False, description="Skip all confirmation prompts")
    skip_backup: bool = Field(
        default=False, description="Skip configuration backup before update"
    )
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)
    continue_on_error: bool = Field(
        default=True, description="Continue with remaining devices if one fails"
    )


class UpdateAvailabilityRequest(BaseModel):
    """Request for checking update availability."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    beta: bool = Field(default=False, description="Check for beta updates")
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=50, gt=0, le=200)


class DeviceUpdateResult(OperationResult):
    """Result of a device update operation."""

    update_initiated: bool = Field(
        default=False, description="Whether the update was successfully initiated"
    )
    previous_version: str | None = Field(default=None)
    target_version: str | None = Field(default=None)
    backup_created: bool = Field(
        default=False, description="Whether configuration backup was created"
    )
    backup_path: str | None = Field(default=None)
    time_taken_seconds: float | None = Field(default=None)


class UpdateAvailabilityResult(OperationResult):
    """Result of update availability check."""

    current_version: str | None = Field(default=None)
    available_version: str | None = Field(default=None)
    update_available: bool = Field(default=False)
    is_beta: bool = Field(
        default=False, description="Whether the available update is beta"
    )
