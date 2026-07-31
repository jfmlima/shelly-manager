"""Use case for acquiring firmware bundles into the local store."""

import asyncio
import hashlib
import logging
import os
import re
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from core.domain.entities.exceptions import FirmwareError
from core.domain.entities.firmware_bundle import FirmwareBundle
from core.domain.value_objects.firmware_release import FirmwareRelease
from core.gateways.firmware import FirmwareGateway
from core.repositories.firmware_repository import FirmwareRepository
from core.settings import FirmwareSettings

logger = logging.getLogger(__name__)

_SAFE_NAME = re.compile(r"[A-Za-z0-9._-]+")


class AcquireFirmware:
    """Download the latest firmware for an app into the local store.

    One download serves every device reporting the same app; a cached bundle
    at the latest version skips the download entirely.
    """

    def __init__(
        self,
        firmware_gateway: FirmwareGateway,
        repository_factory: Callable[
            [], AbstractAsyncContextManager[FirmwareRepository]
        ],
        settings: FirmwareSettings,
    ):
        self._firmware_gateway = firmware_gateway
        self._repository_factory = repository_factory
        self._settings = settings
        self._acquire_lock = asyncio.Lock()

    async def execute(
        self, app_name: str, release: FirmwareRelease | None = None
    ) -> FirmwareBundle:
        """Return the cached bundle at the latest version, downloading on a miss.

        A caller that already resolved the release passes it in, so one update
        never queries the index twice and cannot act on a release that changed
        between the two reads.

        Raises:
            FirmwareError: If the app name is unsafe, the index has no release
                for ``app_name``, or the download fails.
        """
        if not _is_safe_name(app_name):
            raise FirmwareError(
                f"Refusing firmware acquisition for unsafe app name '{app_name}'",
                {"app_name": app_name},
            )

        if release is None:
            release = await self._firmware_gateway.get_latest(app_name)
        if release is None:
            raise FirmwareError(
                f"No firmware published for app '{app_name}'",
                {"app_name": app_name},
            )
        if not _is_safe_name(release.version):
            raise FirmwareError(
                f"Refusing unsafe firmware version '{release.version}'"
                f" from the index for app '{app_name}'",
                {"app_name": app_name, "version": release.version},
            )

        async with self._acquire_lock:
            os.makedirs(self._settings.dir, exist_ok=True)

            async with self._repository_factory() as repository:
                cached = await repository.find(
                    app_name, release.version, release.build_id
                )
            if cached is not None:
                return await self._ensure_on_disk(cached, release)

            file_name = _file_name_for(app_name, release)
            dest_path = os.path.join(self._settings.dir, file_name)
            size_bytes, sha256 = await self._firmware_gateway.download(
                release, dest_path
            )

            bundle = FirmwareBundle(
                app_name=app_name,
                version=release.version,
                build_id=release.build_id,
                file_name=file_name,
                size_bytes=size_bytes,
                sha256=sha256,
            )
            async with self._repository_factory() as repository:
                return await repository.create(bundle)

    async def _ensure_on_disk(
        self, cached: FirmwareBundle, release: FirmwareRelease
    ) -> FirmwareBundle:
        """Return the cached bundle, restoring its zip if it left the disk."""
        path = os.path.join(self._settings.dir, os.path.basename(cached.file_name))
        if os.path.isfile(path):
            logger.info(
                "Firmware cache hit for %s %s (bundle %s)",
                cached.app_name,
                cached.version,
                cached.id,
            )
            return cached

        logger.warning(
            "Firmware bundle %s (%s %s) has no file on disk; re-downloading",
            cached.id,
            cached.app_name,
            cached.version,
        )
        _, sha256 = await self._firmware_gateway.download(release, path)
        if cached.sha256 and sha256 != cached.sha256:
            logger.warning(
                "Re-downloaded firmware bundle %s differs from its stored"
                " sha256; the index republished %s %s",
                cached.id,
                cached.app_name,
                cached.version,
            )
        return cached


def _is_safe_name(value: str) -> bool:
    """Whether the name is safe as a path segment.

    "." and ".." satisfy the character class but are traversal.
    """
    return value not in (".", "..") and bool(_SAFE_NAME.fullmatch(value))


def _file_name_for(app_name: str, release: FirmwareRelease) -> str:
    """A distinct file name per stored bundle identity.

    Rows are unique on (app_name, version, build_id), so the file has to be too
    or deleting one bundle would remove another's zip. The build id is not
    path-safe, and the readable prefix alone is ambiguous ("a-b" with "c" and
    "a" with "b-c" share it), so the hash covers the whole identity joined by a
    byte that validation keeps out of every part.
    """
    identity = "\0".join((app_name, release.version, release.build_id))
    digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
    return f"{app_name}-{release.version}-{digest}.zip"
