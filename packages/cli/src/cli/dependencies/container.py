"""Dependency injection container for CLI using shared BaseContainer."""

from core.dependencies.container_base import BaseContainer
from core.use_cases.scan_devices import ScanDevicesUseCase


class CLIContainer(BaseContainer):
    """CLI container using the shared wiring."""

    def get_device_scan_interactor(self) -> ScanDevicesUseCase:
        """Preserve the legacy convenience name."""
        return self.get_scan_interactor()
