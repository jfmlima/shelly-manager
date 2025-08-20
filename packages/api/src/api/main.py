import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from litestar import Litestar, Router
from litestar.config.cors import CORSConfig

from .controllers.devices import devices_router
from .controllers.monitoring import (
    get_action_history,
    health_check,
)
from .dependencies.container import APIContainer, get_dependencies
from .presentation.handlers import EXCEPTION_HANDLERS


def create_app(config_file_path: str | None = None) -> Litestar:
    _container = APIContainer(config_file_path)

    cors_config = CORSConfig(
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
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
        exception_handlers=EXCEPTION_HANDLERS,
        dependencies=get_dependencies(_container),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        lifespan=[lifespan],
    )

    return app


app = create_app()
