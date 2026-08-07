"""
DiscoveredDevice domain model.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...utils.validation import validate_ip_address
from ..enums.enums import Status


class DiscoveredDevice(BaseModel):
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    ip: str = Field(..., description="Device IP address")
    status: Status = Field(..., description="Current device status")
    device_id: str | None = Field(None, description="Unique device identifier")
    device_type: str | None = Field(None, description="Device model/type")
    app_name: str | None = Field(
        None, description="Device app name firmware is looked up by, e.g. 'Plus2PM'"
    )
    firmware_version: str | None = Field(None, description="Current firmware version")
    available_firmware_version: str | None = Field(
        None, description="Version an available update would install"
    )
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
    def validate_ip(cls, v: str) -> str:
        return validate_ip_address(v)
