"""
Monitoring and health check API routes.
"""

from datetime import datetime
from typing import Any

from litestar import get

from ..dependencies.container import APIContainer

_container = APIContainer()


@get("/health")
async def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "shelly-manager-api",
    }


@get("/actions")
async def get_action_history() -> dict[str, Any]:
    return {
        "success": True,
        "actions": [],
        "message": "Action history not yet implemented",
    }


@get("/devices/updates")
async def get_devices_with_updates() -> dict[str, Any]:
    return {
        "success": True,
        "devices": [],
        "message": "Update checking not yet implemented",
    }
