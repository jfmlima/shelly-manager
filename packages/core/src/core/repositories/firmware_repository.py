"""Abstract repository for cached firmware bundles."""

from abc import ABC, abstractmethod

from core.domain.entities.firmware_bundle import FirmwareBundle


class FirmwareRepository(ABC):
    @abstractmethod
    async def create(self, bundle: FirmwareBundle) -> FirmwareBundle:
        """Persist a bundle. Returns the bundle with its assigned ID.

        Storing a bundle that already exists (same app name, version and
        build ID) returns the existing record instead of failing, so two
        writers racing on one store converge on a single row.
        """
        pass

    @abstractmethod
    async def get(self, bundle_id: int) -> FirmwareBundle | None:
        """Retrieve a bundle by ID."""
        pass

    @abstractmethod
    async def find(
        self, app_name: str, version: str, build_id: str
    ) -> FirmwareBundle | None:
        """Find the cached bundle for one exact release.

        Matches the whole stored identity rather than app and version alone, so
        a version republished under a new build is a miss and gets fetched
        instead of serving the previous build's bytes.
        """
        pass

    @abstractmethod
    async def list(self) -> list[FirmwareBundle]:
        """List every cached bundle, newest first."""
        pass

    @abstractmethod
    async def delete(self, bundle_id: int) -> bool:
        """Delete a bundle by ID. Returns ``True`` if a row was deleted."""
        pass
