"""
ScanRequest domain model.
"""

import ipaddress

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class ScanRequest(BaseModel):

    start_ip: str | None = Field(None, description="Starting IP address for range scan")
    end_ip: str | None = Field(None, description="Ending IP address for range scan")
    use_predefined: bool = Field(
        True, description="Use predefined IPs from configuration"
    )
    use_mdns: bool = Field(False, description="Use mDNS to discover devices")
    timeout: float = Field(
        3.0, ge=0.1, le=30.0, description="Timeout for each device scan"
    )
    max_workers: int = Field(50, ge=1, le=200, description="Maximum concurrent workers")

    @field_validator("start_ip", "end_ip")
    @classmethod
    def validate_ip_addresses(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                ipaddress.IPv4Address(v)
            except ipaddress.AddressValueError as e:
                raise ValueError(f"Invalid IP address: {v}") from e
        return v

    @field_validator("end_ip")
    @classmethod
    def validate_ip_range(cls, v: str | None, info: ValidationInfo) -> str | None:
        if (
            v is not None
            and "start_ip" in info.data
            and info.data["start_ip"] is not None
        ):
            start = ipaddress.IPv4Address(info.data["start_ip"])
            end = ipaddress.IPv4Address(v)
            if start > end:
                raise ValueError("start_ip must be less than or equal to end_ip")
        return v
