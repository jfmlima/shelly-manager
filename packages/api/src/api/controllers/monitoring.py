"""
Monitoring and health check API routes.
"""

from datetime import datetime
from typing import Any

from litestar import get

from ..dependencies.container import APIContainer

_container = APIContainer()


@get("/health", tags=["Health"], summary="Health Check")
async def health_check() -> dict[str, Any]:
    """
    Service health check endpoint.

    Returns the current status of the API service including:
    - Service status
    - Current timestamp
    - API version
    - Service name

    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "shelly-manager-api",
    }
