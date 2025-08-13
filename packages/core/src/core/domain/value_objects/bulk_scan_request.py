"""
Request model for bulk IP scanning.
"""

from pydantic import BaseModel, Field, field_validator

from ...utils.validation import validate_ip_address_list


class BulkScanRequest(BaseModel):
    """Request model for bulk IP scanning."""

    ips: list[str] = Field(
        ..., min_length=1, description="List of IP addresses to scan"
    )
    timeout: float = Field(
        default=3.0, ge=0.1, le=30.0, description="Scan timeout per device"
    )

    @field_validator("ips")
    @classmethod
    def validate_ips(cls, v: list[str]) -> list[str]:
        return validate_ip_address_list(cls, v)
