"""
ScanRequest domain model.
"""

from pydantic import BaseModel, Field, field_validator, model_validator


class ScanRequest(BaseModel):
    """Request to scan for Shelly devices."""

    targets: list[str] = Field(
        default_factory=list,
        description="IP targets: individual IPs, ranges (192.168.1.1-254), or CIDR (192.168.1.0/24)",
    )
    use_mdns: bool = Field(
        False,
        description="Use mDNS to discover devices (ignores targets)",
    )
    timeout: float = Field(
        3.0,
        ge=0.1,
        le=30.0,
        description="Timeout for each device scan in seconds",
    )
    max_workers: int = Field(
        50,
        ge=1,
        le=200,
        description="Maximum concurrent workers",
    )

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: list[str]) -> list[str]:
        """Validate target formats without expanding."""
        if not v:
            return v  # Empty is OK if using mDNS

        from ...utils.target_parser import validate_target

        for target in v:
            try:
                validate_target(target)
            except ValueError as e:
                raise ValueError(f"Invalid target '{target}': {e}") from e

        return v

    @model_validator(mode="after")
    def validate_targets_or_mdns(self) -> "ScanRequest":
        """Validate that either targets or use_mdns is set."""
        if not self.use_mdns and not self.targets:
            raise ValueError(
                "Either 'targets' must be provided or 'use_mdns' must be True"
            )
        return self
