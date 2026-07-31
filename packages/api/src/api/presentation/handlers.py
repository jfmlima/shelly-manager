"""
Exception handlers for the API.

The single place core exceptions become HTTP responses. Controllers raise (or
let escape) core exceptions and never build error responses themselves.
"""

from collections.abc import Callable, MutableMapping
from datetime import datetime
from http import HTTPStatus
from typing import Any

from core.domain.entities.exceptions import (
    BulkOperationError,
    ConfigurationError,
    DeviceAuthenticationError,
    DeviceCommunicationError,
    DeviceNotFoundError,
    FirmwareConfigurationError,
    FirmwareError,
)
from core.domain.entities.exceptions import ValidationError as CoreValidationError
from core.use_cases.backup_device_config import BackupError, BackupNotFoundError
from core.use_cases.manage_backup_schedules import (
    ScheduleAlreadyExistsError,
    ScheduleNotFoundError,
)
from core.use_cases.manage_credentials import CredentialNotFoundError
from core.use_cases.manage_provisioning_profiles import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)
from core.use_cases.restore_device_config import DeviceMismatchError
from litestar.connection import Request
from litestar.exceptions import HTTPException
from litestar.response import Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from pydantic import ValidationError

ExceptionHandler = Callable[[Request[Any, Any, Any], Any], Response[Any]]


def handle_validation_error(request: Request, exc: Exception) -> Response:
    return _error_response("Validation Error", str(exc), 400)


def handle_value_error(request: Request, exc: ValueError) -> Response:
    return _error_response("Bad Request", str(exc), 400)


def handle_device_not_found_error(
    request: Request, exc: DeviceNotFoundError
) -> Response:
    return _error_response("Device Not Found", str(exc), 404, ip=exc.details.get("ip"))


def handle_http_exception(request: Request, exc: HTTPException) -> Response:
    return _error_response(
        HTTPStatus(exc.status_code).phrase, exc.detail, exc.status_code
    )


def handle_generic_exception(request: Request, exc: Exception) -> Response:
    return _error_response(
        "Internal Server Error",
        "An unexpected error occurred",
        HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _error_response(
    error: str, message: str, status_code: int, **extra: Any
) -> Response:
    content = {
        "error": error,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
    content.update({k: v for k, v in extra.items() if v is not None})
    return Response(
        content=content,
        status_code=status_code,
        media_type="application/json",
    )


def _typed_handler(status_code: int, error: str) -> ExceptionHandler:
    def handle(request: Request, exc: Exception) -> Response:
        return _error_response(error, str(exc), status_code)

    return handle


EXCEPTION_HANDLERS: MutableMapping[int | type[Exception], ExceptionHandler] | None = {
    DeviceAuthenticationError: _typed_handler(401, "Authentication Required"),
    DeviceNotFoundError: handle_device_not_found_error,
    DeviceCommunicationError: _typed_handler(502, "Device Communication Error"),
    BulkOperationError: _typed_handler(500, "Bulk Operation Failed"),
    BackupNotFoundError: _typed_handler(404, "Backup Not Found"),
    BackupError: _typed_handler(422, "Backup Error"),
    DeviceMismatchError: _typed_handler(409, "Device Mismatch"),
    FirmwareConfigurationError: _typed_handler(500, "Firmware Not Configured"),
    FirmwareError: _typed_handler(422, "Firmware Error"),
    CredentialNotFoundError: _typed_handler(404, "Credential Not Found"),
    ProfileNotFoundError: _typed_handler(404, "Profile Not Found"),
    ProfileAlreadyExistsError: _typed_handler(409, "Profile Already Exists"),
    ScheduleNotFoundError: _typed_handler(404, "Schedule Not Found"),
    ScheduleAlreadyExistsError: _typed_handler(409, "Schedule Already Exists"),
    CoreValidationError: _typed_handler(400, "Validation Error"),
    ConfigurationError: _typed_handler(500, "Configuration Error"),
    ValueError: handle_value_error,
    HTTPException: handle_http_exception,
    Exception: handle_generic_exception,
    ValidationError: handle_validation_error,
}
