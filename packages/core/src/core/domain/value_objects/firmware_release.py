"""Firmware release value objects."""

from pydantic import BaseModel, ConfigDict, Field


class FirmwareRelease(BaseModel):
    """A downloadable firmware build published in the Shelly update index."""

    model_config = ConfigDict(frozen=True)

    app_name: str = Field(..., description="Device app name, e.g. 'Plus2PM'")
    version: str = Field(..., description="Firmware version, e.g. '1.7.5'")
    build_id: str = Field(..., description="Full build identifier")
    download_url: str = Field(..., description="Direct download URL for the bundle")
    channel: str = Field(default="stable", description="Release channel (stable/beta)")
