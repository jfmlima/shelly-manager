"""
Data models for Shelly device management.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


class DeviceStatus(Enum):
    """Device scan status enumeration."""
    DETECTED = "detected"
    UPDATED = "updated"
    NO_UPDATE_NEEDED = "no_update_needed"
    AUTH_REQUIRED = "auth_required"
    NOT_SHELLY = "not_shelly"
    UNREACHABLE = "unreachable"
    ERROR = "error"


@dataclass
class ShellyDevice:
    """Represents a discovered Shelly device."""
    ip: str
    status: DeviceStatus
    device_id: Optional[str] = None
    device_type: Optional[str] = None
    firmware_version: Optional[str] = None
    device_name: Optional[str] = None
    auth_required: bool = False
    last_seen: Optional[str] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        return result
