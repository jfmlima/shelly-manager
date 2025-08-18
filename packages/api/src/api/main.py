"""
Main Litestar application setup using core.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from litestar import Litestar, Router
from litestar.config.cors import CORSConfig
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.response import Response
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR
from pydantic import ValidationError

from .controllers.devices import devices_router
from .controllers.monitoring import (
    get_action_history,
    health_check,
)
from .dependencies.container import APIContainer


def create_app(config_file_path: str | None = None) -> Litestar:
    _container = APIContainer(config_file_path)

    cors_config = CORSConfig(
        allow_origins=["*"],  # Configure based on your needs
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    def handle_validation_error(request: Any, exc: Exception) -> Response:
        return Response(
            content={
                "error": "Validation Error",
                "message": str(exc),
                "timestamp": datetime.now().isoformat(),
            },
            status_code=400,
            media_type="application/json",
        )

    def handle_value_error(request: Any, exc: ValueError) -> Response:
        return Response(
            content={
                "error": "Bad Request",
                "message": str(exc),
                "timestamp": datetime.now().isoformat(),
            },
            status_code=400,
            media_type="application/json",
        )

    def handle_http_exception(request: Any, exc: HTTPException) -> Response:
        return Response(
            content={
                "error": exc.detail,
                "message": f"HTTP {exc.status_code}",
                "timestamp": datetime.now().isoformat(),
            },
            status_code=exc.status_code,
            media_type="application/json",
        )

    def handle_generic_exception(request: Any, exc: Exception) -> Response:
        return Response(
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.now().isoformat(),
            },
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json",
        )

    api_router = Router(
        path="/api",
        route_handlers=[
            devices_router,
            health_check,
            get_action_history,
        ],
    )

    @asynccontextmanager
    async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
        try:
            yield
        finally:
            await _container.close()

    app = Litestar(
        route_handlers=[api_router],
        cors_config=cors_config,
        exception_handlers={
            ValueError: handle_value_error,
            HTTPException: handle_http_exception,
            Exception: handle_generic_exception,
            ValidationError: handle_validation_error,
        },
        dependencies={
            "scan_interactor": Provide(
                lambda: _container.get_scan_interactor(), sync_to_thread=False
            ),
            "update_interactor": Provide(
                lambda: _container.get_update_interactor(), sync_to_thread=False
            ),
            "reboot_interactor": Provide(
                lambda: _container.get_reboot_interactor(), sync_to_thread=False
            ),
            "status_interactor": Provide(
                lambda: _container.get_status_interactor(), sync_to_thread=False
            ),
            "get_config_interactor": Provide(
                lambda: _container.get_device_config_interactor(), sync_to_thread=False
            ),
            "set_config_interactor": Provide(
                lambda: _container.get_device_config_set_interactor(),
                sync_to_thread=False,
            ),
        },
        debug=os.getenv("DEBUG", "false").lower() == "true",
        lifespan=[lifespan],
    )

    return app


app = create_app()
