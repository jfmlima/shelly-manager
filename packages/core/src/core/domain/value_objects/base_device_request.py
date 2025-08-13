"""
Base request models for device operations.
"""

from pydantic import BaseModel, Field, field_validator

from ...utils.validation import validate_ip_address, validate_ip_address_list


class BaseDeviceRequest(BaseModel):
    """Base request model for single device operations."""

    device_ip: str = Field(..., description="IP address of the device")

    @field_validator("device_ip")
    @classmethod
    def validate_device_ip(cls, v: str) -> str:
        return validate_ip_address(cls, v)


class BaseBulkDeviceRequest(BaseModel):
    """Base request model for bulk device operations."""

    device_ips: list[str] = Field(
        ..., min_length=1, description="List of device IP addresses"
    )

    @field_validator("device_ips")
    @classmethod
    def validate_device_ips(cls, v: list[str]) -> list[str]:
        return validate_ip_address_list(cls, v)
