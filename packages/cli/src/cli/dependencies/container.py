"""Dependency injection container for CLI using shared BaseContainer."""

from core.dependencies.container_base import BaseContainer
from core.repositories.db import engine
from core.repositories.models import Base
from core.use_cases.scan_devices import ScanDevicesUseCase


class CLIContainer(BaseContainer):
    """CLI container using the shared wiring."""

    async def initialize_database(self) -> None:
        """Create the database schema required by standalone CLI commands."""
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await super().close()
        await engine.dispose()

    def get_device_scan_interactor(self) -> ScanDevicesUseCase:
        """Preserve the legacy convenience name."""
        return self.get_scan_interactor()
