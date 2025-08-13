"""
Request model for bulk status check.
"""

from pydantic import Field

from .base_device_request import BaseBulkDeviceRequest


class BulkStatusRequest(BaseBulkDeviceRequest):
    """Request model for bulk status check."""

    include_updates: bool = Field(
        default=True, description="Whether to include update information"
    )
