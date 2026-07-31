"""Use case for browsing and pruning the local firmware store."""

import logging
import os
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path

from core.domain.entities.firmware_bundle import FirmwareBundle
from core.repositories.firmware_repository import FirmwareRepository
from core.settings import FirmwareSettings

logger = logging.getLogger(__name__)


class ManageFirmware:
    """List cached firmware bundles, resolve their zips on disk, delete them."""

    def __init__(
        self,
        repository_factory: Callable[
            [], AbstractAsyncContextManager[FirmwareRepository]
        ],
        settings: FirmwareSettings,
    ):
        self._repository_factory = repository_factory
        self._settings = settings

    async def list_bundles(self) -> list[FirmwareBundle]:
        async with self._repository_factory() as repository:
            return await repository.list()

    async def get_bundle(self, bundle_id: int) -> FirmwareBundle | None:
        async with self._repository_factory() as repository:
            return await repository.get(bundle_id)

    async def delete_bundle(self, bundle_id: int) -> bool:
        """Delete a bundle's metadata and its zip. Returns ``True`` if it existed."""
        async with self._repository_factory() as repository:
            bundle = await repository.get(bundle_id)
            if bundle is None:
                return False
            deleted = await repository.delete(bundle_id)
        if deleted:
            Path(self.bundle_path(bundle)).unlink(missing_ok=True)
            logger.info(
                "Deleted firmware bundle %s (%s %s)",
                bundle_id,
                bundle.app_name,
                bundle.version,
            )
        return deleted

    def bundle_path(self, bundle: FirmwareBundle) -> str:
        """Where a bundle's zip lives, always inside the firmware directory."""
        return os.path.join(self._settings.dir, os.path.basename(bundle.file_name))
