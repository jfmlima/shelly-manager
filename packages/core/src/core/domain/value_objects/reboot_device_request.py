"""
Request model for rebooting a device.
"""

from typing import Optional

from pydantic import Field

from .base_device_request import BaseDeviceRequest


class RebootDeviceRequest(BaseDeviceRequest):
    """Request model for rebooting a device."""

    delay: Optional[int] = Field(None, description="Delay before reboot in seconds")
    force: Optional[bool] = Field(None, description="Force reboot without graceful shutdown")
    username: Optional[str] = Field(None, description="Authentication username")
    password: Optional[str] = Field(None, description="Authentication password")
    timeout: Optional[float] = Field(None, description="Request timeout in seconds")
