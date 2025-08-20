"""
Custom HTTP exceptions for the API.
"""

from litestar.exceptions import HTTPException


class DeviceNotFoundHTTPException(HTTPException):
    """Custom HTTP exception for device not found scenarios."""

    def __init__(self, device_ip: str, message: str | None = None):
        """
        Initialize DeviceNotFoundHTTPException.

        Args:
            device_ip: The IP address of the device that was not found
            message: Optional custom message, defaults to standard message
        """
        self.device_ip = device_ip
        detail = message or f"Device not found or unreachable: {device_ip}"
        super().__init__(status_code=404, detail=detail)
