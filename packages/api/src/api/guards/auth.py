"""
Guard enforcing the optional shared auth token.
"""

import hmac

from core.domain.entities.exceptions import UnauthorizedError
from core.settings import settings
from litestar.connection import ASGIConnection
from litestar.handlers.base import BaseRouteHandler


def require_auth(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Reject the request unless it carries the configured auth token.

    A no-op when SHELLY_AUTH_TOKEN is unset, preserving the zero-config
    default of no authentication.
    """
    token = settings.auth_token
    if not token:
        return

    header = connection.headers.get("authorization", "")
    presented = header.removeprefix("Bearer ") if header.startswith("Bearer ") else ""
    if not presented or not hmac.compare_digest(presented, token):
        raise UnauthorizedError()
