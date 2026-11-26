"""
Bulk operation entities for CLI operations.
"""

from typing import Any

from pydantic import BaseModel, Field


class BulkOperationRequest(BaseModel):
    targets: list[str] = Field(
        default_factory=list,
        description="List of IP targets (e.g., ['192.168.1.1', '192.168.1.0/24'])",
    )
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)
    force: bool = Field(default=False, description="Skip confirmation prompts")


class BulkConfigExportRequest(BulkOperationRequest):
    component_types: list[str] = Field(
        description="Component types to export (e.g., switch, input)"
    )
    output_file: str = Field(description="Output file path for exported configuration")


class BulkConfigApplyRequest(BulkOperationRequest):
    component_type: str = Field(description="Single component type to apply config to")
    config_file: str | None = Field(
        default=None, description="Path to configuration file"
    )
    config_data: dict[str, Any] | None = Field(
        default=None, description="Configuration data directly"
    )
