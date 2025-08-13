"""
Request model for checking device status.
"""

from pydantic import Field

from .base_device_request import BaseDeviceRequest


class CheckDeviceStatusRequest(BaseDeviceRequest):
    """Request model for checking device status."""

    include_updates: bool = Field(
        default=True, description="Whether to include update information"
    )
