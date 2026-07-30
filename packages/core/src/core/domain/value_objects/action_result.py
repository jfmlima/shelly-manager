"""
ActionResult domain model.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from ...utils.validation import validate_ip_address


class ActionResult(BaseModel):

    success: bool = Field(..., description="Whether the action was successful")
    action_type: str = Field(..., description="Type of action that was performed")
    device_ip: str = Field(..., description="Target device IP address")
    message: str = Field(..., description="Human-readable result message")
    data: dict[str, Any] | None = Field(None, description="Additional result data")
    error: str | None = Field(None, description="Error message if action failed")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When the action completed"
    )

    @field_validator("device_ip")
    @classmethod
    def validate_device_ip(cls, v: str) -> str:
        return validate_ip_address(v)
