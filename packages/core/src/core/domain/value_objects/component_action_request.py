"""
Component action request value objects.
"""

from typing import Any

from pydantic import Field

from .base_device_request import BaseDeviceRequest


class ComponentActionRequest(BaseDeviceRequest):
    """Request for executing action on device component."""

    component_key: str = Field(
        ..., description="Component key (e.g., 'switch:0', 'sys', 'zigbee')"
    )
    action: str = Field(
        ..., description="Action name (e.g., 'Toggle', 'Reboot', 'Update')"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific parameters (e.g., {'channel': 'beta', 'output': True})",
    )
