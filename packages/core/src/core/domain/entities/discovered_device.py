"""
DiscoveredDevice domain model.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from ...utils.validation import validate_ip_address
from ..enums.enums import Status, UpdateChannel
from ..model_names import get_model_name


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
    available_firmware_channel: UpdateChannel | None = Field(
        None,
        description="Channel the available update was found on",
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def model_name(self) -> str | None:
        """Friendly marketing name for device_type, None when unmapped."""
        return get_model_name(self.device_type)

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        return validate_ip_address(v)

    def is_beta_only_update(self) -> bool:
        """The device has an available update, but only on the beta channel.

        Stable wins when both channels have a release, so a beta channel here
        means beta is the only option.
        """
        return (
            self.status == Status.UPDATE_AVAILABLE
            and self.available_firmware_channel == UpdateChannel.BETA
        )
