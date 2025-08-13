"""
Request model for updating device firmware.
"""

from pydantic import Field

from ..enums.enums import UpdateChannel
from .base_device_request import BaseDeviceRequest


class UpdateDeviceFirmwareRequest(BaseDeviceRequest):
    """Request model for updating device firmware."""

    channel: UpdateChannel = Field(
        default=UpdateChannel.STABLE, description="Update channel (stable or beta)"
    )
    force: bool = Field(default=False, description="Force update even if not needed")
