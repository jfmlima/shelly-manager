"""
Exception handlers for the API.
"""

from collections.abc import Callable, MutableMapping
from datetime import datetime
from typing import Any

from litestar.connection import Request
from litestar.exceptions import HTTPException
from litestar.response import Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from pydantic import ValidationError

from .exceptions import DeviceNotFoundHTTPException


def handle_validation_error(request: Request, exc: Exception) -> Response:
    return Response(
        content={
            "error": "Validation Error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat(),
        },
        status_code=400,
        media_type="application/json",
    )


def handle_value_error(request: Request, exc: ValueError) -> Response:
    return Response(
        content={
            "error": "Bad Request",
            "message": str(exc),
            "timestamp": datetime.now().isoformat(),
        },
        status_code=400,
        media_type="application/json",
    )


def handle_device_not_found_exception(
    request: Request, exc: DeviceNotFoundHTTPException
) -> Response:
    return Response(
        content={
            "error": "Device Not Found",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "ip": exc.device_ip,
        },
        status_code=404,
        media_type="application/json",
    )


def handle_http_exception(request: Request, exc: HTTPException) -> Response:
    return Response(
        content={
            "error": exc.detail,
            "message": f"HTTP {exc.status_code}",
            "timestamp": datetime.now().isoformat(),
        },
        status_code=exc.status_code,
        media_type="application/json",
    )


def handle_generic_exception(request: Request, exc: Exception) -> Response:
    return Response(
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat(),
        },
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/json",
    )


EXCEPTION_HANDLERS: (
    MutableMapping[
        int | type[Exception], Callable[[Request[Any, Any, Any], Any], Response[Any]]
    ]
    | None
) = {
    DeviceNotFoundHTTPException: handle_device_not_found_exception,
    ValueError: handle_value_error,
    HTTPException: handle_http_exception,
    Exception: handle_generic_exception,
    ValidationError: handle_validation_error,
}
