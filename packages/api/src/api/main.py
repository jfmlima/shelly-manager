import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from litestar import Litestar, Router
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.config import Contact, License, Server, Tag

from .controllers.devices import devices_router
from .controllers.monitoring import (
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

    openapi_config = OpenAPIConfig(
        title="Shelly Manager API",
        version="1.0.0",
        description="Local management for Shelly IoT devices without cloud connectivity",
        summary="Manage Shelly devices on your local network - scan for devices, update firmware, manage configurations, and monitor status.",
        contact=Contact(
            name="Shelly Manager",
            url="https://github.com/jfmlima/shelly-manager",
        ),
        license=License(
            name="MIT",
            url="https://opensource.org/licenses/MIT",
        ),
        tags=[
            Tag(name="Health", description="Service health and monitoring"),
            Tag(name="Devices", description="Device discovery and management"),
            Tag(name="Components", description="Device component actions"),
            Tag(name="Configuration", description="Device configuration management"),
        ],
        servers=[
            Server(url="http://localhost:8000", description="Development server"),
        ],
        use_handler_docstrings=True,
        path="/docs",
        root_schema_site="swagger",
        enabled_endpoints={"swagger", "openapi.json"},
    )

    api_router = Router(
        path="/api",
        route_handlers=[
            devices_router,
            health_check,
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
        openapi_config=openapi_config,
        exception_handlers=EXCEPTION_HANDLERS,
        dependencies=get_dependencies(_container),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        lifespan=[lifespan],
    )

    return app


app = create_app()
