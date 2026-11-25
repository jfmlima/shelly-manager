"""Dependency injection container for CLI using shared BaseContainer."""

from core.dependencies.container_base import BaseContainer
from core.repositories.db import engine


class CLIContainer(BaseContainer):
    """CLI container using the shared wiring."""

    async def close(self) -> None:
        await super().close()
        await engine.dispose()
