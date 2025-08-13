"""
Request model for bulk configuration operations.
"""

from typing import Any

from pydantic import Field

from .base_device_request import BaseBulkDeviceRequest


class BulkConfigurationRequest(BaseBulkDeviceRequest):
    """Request model for bulk configuration operations."""

    config: dict[str, Any] = Field(..., description="Configuration to set")
