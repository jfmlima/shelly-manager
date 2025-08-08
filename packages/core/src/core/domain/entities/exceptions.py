"""
Custom exception types for the Shelly Manager application.
"""

from typing import Any


class ShellyManagerError(Exception):

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DeviceNotFoundError(ShellyManagerError):

    def __init__(self, ip: str, message: str | None = None):
        msg = message or f"Device not found or unreachable: {ip}"
        super().__init__(msg, {"ip": ip})


class DeviceAuthenticationError(ShellyManagerError):

    def __init__(self, ip: str, message: str | None = None):
        msg = message or f"Authentication failed for device: {ip}"
        super().__init__(msg, {"ip": ip})


class DeviceCommunicationError(ShellyManagerError):

    def __init__(self, ip: str, error: str, message: str | None = None):
        msg = message or f"Communication error with device {ip}: {error}"
        super().__init__(msg, {"ip": ip, "error": error})


class ConfigurationError(ShellyManagerError):

    def __init__(self, operation: str, message: str | None = None):
        msg = message or f"Configuration error during {operation}"
        super().__init__(msg, {"operation": operation})


class ValidationError(ShellyManagerError):

    def __init__(self, field: str, value: Any, message: str | None = None):
        msg = message or f"Validation error for field '{field}' with value '{value}'"
        super().__init__(msg, {"field": field, "value": value})


class NetworkError(ShellyManagerError):

    def __init__(self, operation: str, error: str, message: str | None = None):
        msg = message or f"Network error during {operation}: {error}"
        super().__init__(msg, {"operation": operation, "error": error})


class ActionExecutionError(ShellyManagerError):

    def __init__(
        self,
        action_type: str,
        device_ip: str,
        error: str,
        message: str | None = None,
    ):
        msg = message or f"Action '{action_type}' failed on device {device_ip}: {error}"
        super().__init__(
            msg, {"action_type": action_type, "device_ip": device_ip, "error": error}
        )


class BulkOperationError(ShellyManagerError):

    def __init__(
        self, operation: str, failed_devices: list[str], message: str | None = None
    ):
        msg = (
            message
            or f"Bulk operation '{operation}' failed on devices: {', '.join(failed_devices)}"
        )
        super().__init__(
            msg, {"operation": operation, "failed_devices": failed_devices}
        )


class ExportError(ShellyManagerError):

    def __init__(self, format: str, error: str, message: str | None = None):
        msg = message or f"Export error for format '{format}': {error}"
        super().__init__(msg, {"format": format, "error": error})


class LoggingError(ShellyManagerError):

    def __init__(self, operation: str, error: str, message: str | None = None):
        msg = message or f"Logging error during {operation}: {error}"
        super().__init__(msg, {"operation": operation, "error": error})


class DomainError(ShellyManagerError):

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, details)


class DeviceValidationError(DomainError):

    def __init__(self, device_ip: str, message: str | None = None):
        msg = message or f"Device validation failed: {device_ip}"
        super().__init__(msg, {"device_ip": device_ip})
