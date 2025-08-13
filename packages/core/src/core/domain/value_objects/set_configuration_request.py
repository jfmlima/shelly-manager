"""
Request model for setting device configuration.
"""

from typing import Any

from pydantic import Field

from .device_configuration_request import DeviceConfigurationRequest


class SetConfigurationRequest(DeviceConfigurationRequest):
    """Request model for setting device configuration."""

    config: dict[str, Any] = Field(..., description="Configuration to set")
