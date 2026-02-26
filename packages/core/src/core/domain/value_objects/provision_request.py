"""Value objects for device provisioning."""

from dataclasses import dataclass, field

from pydantic import BaseModel, Field, field_validator

# Default AP IP address for Shelly devices
DEFAULT_AP_IP = "192.168.33.1"


class ProvisionDeviceRequest(BaseModel):
    """Request to provision a new Shelly device via its AP."""

    device_ip: str = Field(
        default=DEFAULT_AP_IP,
        description="IP address of the device in AP mode",
    )
    profile_id: int | None = Field(
        default=None,
        description="Provisioning profile ID. None uses the default profile.",
    )
    timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Timeout for each RPC call in seconds",
    )
    verify_timeout: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="Timeout for post-provision verification scan",
    )

    @field_validator("device_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        import ipaddress

        try:
            ipaddress.IPv4Address(v)
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid IP address: {v}") from e
        return v


class DetectDeviceRequest(BaseModel):
    """Request to detect a device at an AP IP."""

    device_ip: str = Field(
        default=DEFAULT_AP_IP,
        description="IP address of the device in AP mode",
    )
    timeout: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Timeout in seconds",
    )

    @field_validator("device_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        import ipaddress

        try:
            ipaddress.IPv4Address(v)
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid IP address: {v}") from e
        return v


@dataclass
class APDeviceInfo:
    """Information about a device detected in AP mode."""

    device_id: str
    mac: str
    model: str
    generation: int
    firmware_version: str
    auth_enabled: bool
    auth_domain: str | None = None
    app: str | None = None


@dataclass
class ProvisionStep:
    """Result of a single provisioning step."""

    name: str
    success: bool
    message: str | None = None
    restart_required: bool = False


@dataclass
class ProvisionResult:
    """Result of a full device provisioning operation."""

    success: bool
    device_id: str | None = None
    device_model: str | None = None
    device_mac: str | None = None
    generation: int | None = None
    steps_completed: list[ProvisionStep] = field(default_factory=list)
    steps_failed: list[ProvisionStep] = field(default_factory=list)
    final_ip: str | None = None
    error: str | None = None
    needs_verification: bool = False
