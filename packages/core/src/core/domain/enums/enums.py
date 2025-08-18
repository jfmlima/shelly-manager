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
