"""
Export-related entities for CLI operations.
"""

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    """Request for exporting device configurations."""

    targets: list[str] = Field(
        default_factory=list,
        description="IP targets: individual IPs, ranges, or CIDR notation",
    )
    format: str = Field(
        default="json",
        pattern=r"^(json|csv|yaml)$",
        description="Export format (json, csv or yaml)",
    )
    timeout: float = Field(default=3.0, gt=0)
    output: str | None = Field(default=None, description="Output file path")
    force: bool = Field(default=False, description="Force overwrite without prompt")
    include_config: bool = Field(
        default=True, description="Include device configuration"
    )
    pretty: bool = Field(default=False, description="Pretty print output")
