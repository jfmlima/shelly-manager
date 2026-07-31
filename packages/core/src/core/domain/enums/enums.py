"""
Core enumerations for Shelly device management.
"""

from enum import Enum


class Status(str, Enum):

    DETECTED = "detected"
    UPDATED = "updated"
    UPDATE_AVAILABLE = "update_available"
    NO_UPDATE_NEEDED = "no_update_needed"
    AUTH_REQUIRED = "auth_required"
    NOT_SHELLY = "not_shelly"
    UNREACHABLE = "unreachable"
    ERROR = "error"


class UpdateChannel(str, Enum):

    STABLE = "stable"
    BETA = "beta"

    def to_update_parameters(self) -> dict[str, str]:
        """Parameters for a firmware Update action.

        Shelly.Update names this field stage. A device silently ignores an
        unknown parameter, so sending channel installed stable no matter what
        was asked for. Stable is the device-side default and sends nothing.
        """
        if self is UpdateChannel.STABLE:
            return {}
        return {"stage": self.value}
