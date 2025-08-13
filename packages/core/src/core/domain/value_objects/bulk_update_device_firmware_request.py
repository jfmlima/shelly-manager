"""
Request model for bulk updating device firmware.
"""

from pydantic import Field

from ..enums.enums import UpdateChannel
from .base_device_request import BaseBulkDeviceRequest


class BulkUpdateDeviceFirmwareRequest(BaseBulkDeviceRequest):
    """Request model for bulk updating device firmware."""

    channel: UpdateChannel = Field(
        default=UpdateChannel.STABLE, description="Update channel (stable or beta)"
    )
    force: bool = Field(default=False, description="Force update even if not needed")
