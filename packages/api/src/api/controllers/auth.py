"""
Auth API routes for the optional shared auth token.
"""

from core.settings import settings
from litestar import Router, get

from ..guards.auth import require_auth


@get("/config", tags=["Auth"], summary="Auth Configuration")
async def get_auth_config() -> dict[str, bool]:
    """
    Whether the API currently requires authentication.

    Always public, since the Web UI needs to know whether to show the
    login page before it has (or needs) a token of its own.

    Returns:
        dict: {"enabled": bool}
    """
    return {"enabled": bool(settings.auth_token)}


@get("/verify", tags=["Auth"], summary="Verify Token", guards=[require_auth])
async def verify_token() -> dict[str, bool]:
    """
    Confirm a bearer token is valid.

    Only reached if the guard already accepted the Authorization header;
    a missing/invalid token never reaches this handler.

    Returns:
        dict: {"valid": true}
    """
    return {"valid": True}


auth_router = Router(path="/auth", route_handlers=[get_auth_config, verify_token])
