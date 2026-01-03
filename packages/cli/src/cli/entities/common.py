"""
Common entities and validators for CLI operations.
"""

import ipaddress

from pydantic import BaseModel, Field, field_validator


class DeviceDiscoveryRequest(BaseModel):
    """Request for discovering devices through various methods."""

    targets: list[str] = Field(
        default_factory=list,
        description="List of IP targets (e.g., ['192.168.1.1', '192.168.1.0/24'])",
    )
    use_mdns: bool = Field(
        default=False, description="Whether to discover devices via mDNS"
    )
    timeout: float = Field(default=3.0, gt=0, description="Request timeout in seconds")
    workers: int = Field(
        default=50, gt=0, le=200, description="Maximum number of concurrent workers"
    )

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: list[str]) -> list[str]:
        if not v:
            return v

        from core.utils.target_parser import validate_target

        for target in v:
            try:
                validate_target(target)
            except ValueError as e:
                raise ValueError(f"Invalid target: {target} - {str(e)}") from e
        return v


class OperationResult(BaseModel):
    """Base class for operation results."""

    ip: str = Field(description="Device IP address")
    status: str = Field(description="Operation status (success, failed, error)")
    message: str | None = Field(
        default=None, description="Success or informational message"
    )
    error: str | None = Field(
        default=None, description="Error message if operation failed"
    )

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {v}") from e
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status values."""
        allowed_statuses = {"success", "failed", "error", "up_to_date", "pending"}
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {allowed_statuses}")
        return v
