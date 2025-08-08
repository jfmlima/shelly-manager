"""
Common entities and validators for CLI operations.
"""

import ipaddress

from pydantic import BaseModel, Field, field_validator


class DeviceDiscoveryRequest(BaseModel):
    """Request for discovering devices through various methods."""

    ip_ranges: list[str] = Field(
        default_factory=list,
        description="List of IP ranges to scan (e.g., ['192.168.1.1-192.168.1.50'])",
    )
    devices: list[str] = Field(
        default_factory=list, description="List of specific device IP addresses"
    )
    from_config: bool = Field(
        default=False, description="Whether to discover devices from configuration"
    )
    timeout: float = Field(default=3.0, gt=0, description="Request timeout in seconds")
    workers: int = Field(
        default=50, gt=0, le=200, description="Maximum number of concurrent workers"
    )

    @field_validator("devices")
    @classmethod
    def validate_device_ips(cls, v: list[str]) -> list[str]:
        for ip in v:
            try:
                ipaddress.ip_address(ip)
            except ValueError as e:
                raise ValueError(f"Invalid IP address: {ip}") from e
        return v

    @field_validator("ip_ranges")
    @classmethod
    def validate_ip_ranges(cls, v: list[str]) -> list[str]:
        for ip_range in v:
            if "-" in ip_range:
                # Validate range format (e.g., "192.168.1.1-192.168.1.50")
                start, end = ip_range.split("-", 1)
                try:
                    ipaddress.ip_address(start.strip())
                    ipaddress.ip_address(end.strip())
                except ValueError as e:
                    raise ValueError(f"Invalid IP range: {ip_range}") from e
            elif "/" in ip_range:
                # Validate CIDR format (e.g., "192.168.1.0/24")
                try:
                    ipaddress.ip_network(ip_range, strict=False)
                except ValueError as e:
                    raise ValueError(f"Invalid CIDR notation: {ip_range}") from e
            else:
                # Single IP
                try:
                    ipaddress.ip_address(ip_range)
                except ValueError as e:
                    raise ValueError(f"Invalid IP address: {ip_range}") from e
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
