"""Result value objects for device configuration restore operations."""

from pydantic import BaseModel, Field


class ComponentRestoreResult(BaseModel):
    """Outcome of restoring a single component from a backup."""

    key: str = Field(..., description="Component key, e.g. 'switch:0'")
    action: str = Field(..., description="RPC action attempted, e.g. 'SetConfig'")
    success: bool = Field(..., description="Whether the component was restored")
    skipped: bool = Field(
        default=False, description="Whether the component was skipped"
    )
    skipped_reason: str | None = Field(
        default=None, description="Why the component was skipped, if applicable"
    )
    error: str | None = Field(default=None, description="Error message if it failed")


class RestoreResult(BaseModel):
    """Aggregated outcome of restoring a backup to a device."""

    success: bool = Field(..., description="True if no component failed")
    device_ip: str = Field(..., description="Target device IP address")
    backup_id: int = Field(..., description="ID of the backup that was restored")
    total: int = Field(..., description="Total components considered")
    succeeded: int = Field(default=0, description="Components restored successfully")
    failed: int = Field(default=0, description="Components that failed to restore")
    skipped: int = Field(default=0, description="Components that were skipped")
    message: str | None = Field(default=None, description="Optional summary message")
    components: list[ComponentRestoreResult] = Field(
        default_factory=list, description="Per-component results"
    )
