"""
DiscoveredDevice domain model.
"""

import ipaddress
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..enums.enums import Status


class DiscoveredDevice(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    ip: str = Field(..., description="Device IP address")
    status: Status = Field(..., description="Current device status")
    device_id: str | None = Field(None, description="Unique device identifier")
    device_type: str | None = Field(None, description="Device model/type")
    firmware_version: str | None = Field(None, description="Current firmware version")
    device_name: str | None = Field(None, description="User-defined device name")
    auth_required: bool = Field(
        False, description="Whether device requires authentication"
    )
    last_seen: datetime | None = Field(None, description="Last time device was seen")
    response_time: float | None = Field(
        None, ge=0, description="Last response time in seconds"
    )
    error_message: str | None = Field(None, description="Last error message if any")
    has_update: bool = Field(False, description="Whether firmware update is available")

    @field_validator("ip")
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        try:
            ipaddress.IPv4Address(v)
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid IP address: {v}") from e
        return v
