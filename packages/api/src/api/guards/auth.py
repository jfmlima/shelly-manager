"""
Guard enforcing the optional shared auth token.
"""

import hmac

from core.settings import settings
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler


def require_auth(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Reject the request unless it carries the configured auth token.

    A no-op when SHELLY_AUTH_TOKEN is unset, preserving the zero-config
    default of no authentication.

    The 401 carries ``WWW-Authenticate: Bearer`` (RFC 7235) so the Web UI can
    tell a manager logout apart from a device's own 401.
    """
    token = settings.auth_token
    if not token:
        return

    header = connection.headers.get("authorization", "")
    presented = header.removeprefix("Bearer ") if header.startswith("Bearer ") else ""
    if not presented or not hmac.compare_digest(presented.encode(), token.encode()):
        raise NotAuthorizedException(
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
