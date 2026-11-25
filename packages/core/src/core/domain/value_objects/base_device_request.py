"""
Base request models for device operations.
"""

from pydantic import BaseModel, Field, field_validator

from ...utils.validation import validate_ip_address


class BaseDeviceRequest(BaseModel):
    """Base request model for single device operations."""

    device_ip: str = Field(..., description="IP address of the device")

    @field_validator("device_ip")
    @classmethod
    def validate_device_ip(cls, v: str) -> str:
        return validate_ip_address(v)
