"""
Monitoring and health check API routes.
"""

from datetime import datetime
from typing import Any

from litestar import get

from ..dependencies.container import APIContainer

_container = APIContainer()


@get("/health")  # type: ignore[misc]
async def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "shelly-manager-api",
    }


@get("/actions")  # type: ignore[misc]
async def get_action_history() -> dict[str, Any]:
    return {
        "success": True,
        "actions": [],
        "message": "Action history not yet implemented",
    }
