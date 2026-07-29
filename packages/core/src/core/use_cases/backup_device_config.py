"""Use case for capturing and managing device configuration backups."""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from core.domain.entities.config_snapshot import SCHEDULES_KEY
from core.domain.entities.device_backup import (
    BackupPage,
    DeviceBackup,
    DeviceBackupSummary,
)
from core.domain.entities.exceptions import DeviceNotFoundError
from core.domain.value_objects.generation import Generation
from core.gateways.device import DeviceGateway
from core.repositories.backup_repository import BackupRepository
from core.use_cases.capture_device_config import CaptureDeviceConfig

logger = logging.getLogger(__name__)


class BackupNotFoundError(Exception):
    """Raised when a backup is not found."""

    def __init__(self, backup_id: int):
        self.backup_id = backup_id
        super().__init__(f"Backup not found: {backup_id}")


class BackupError(Exception):
    """Raised when a backup cannot be captured."""


class BackupDeviceConfig:
    """Capture a full configuration snapshot of a single device and persist it.

    Shares ``CaptureDeviceConfig`` with the bulk export, so a stored snapshot is
    identical in shape to the bulk-export block for one device.
    """

    def __init__(
        self,
        device_gateway: DeviceGateway,
        capture: CaptureDeviceConfig,
        repository_factory: Callable[[], AbstractAsyncContextManager[BackupRepository]],
    ):
        self._device_gateway = device_gateway
        self._capture = capture
        self._repository_factory = repository_factory

    async def create_backup(
        self,
        device_ip: str,
        name: str | None = None,
        source: str = "manual",
    ) -> DeviceBackup:
        """Snapshot every component config on a device and persist it.

        Raises:
            DeviceNotFoundError: If the device is unreachable.
            BackupError: If the device MAC cannot be determined.
        """
        status = await self._device_gateway.get_device_status(device_ip)
        if status is None:
            raise DeviceNotFoundError(device_ip)

        component_types = sorted(
            {component.component_type for component in status.components}
            | {SCHEDULES_KEY}
        )
        snapshot = await self._capture.capture(device_ip, status, component_types)
        if not snapshot.has_restorable_payload:
            raise BackupError(
                f"No restorable configuration captured for {device_ip}; "
                "backup aborted"
            )

        mac = status.mac_address or snapshot.device_info.mac_address
        if not mac:
            raise BackupError(
                f"Could not determine MAC address for device {device_ip}; "
                "backup aborted"
            )

        # Generation comes from the device's explicit `gen` field (Gen2+ RPC) or
        # the legacy gateway's gen=1 stamp, never inferred from a missing field.
        generation = Generation.from_device_gen(status.gen)
        if generation is None:
            raise BackupError(
                f"Could not determine device generation for {device_ip}; "
                "backup aborted"
            )

        backup = DeviceBackup(
            device_mac=mac,
            snapshot=snapshot.to_dict(),
            device_ip=device_ip,
            device_name=status.device_name,
            device_type=status.device_type,
            firmware_version=status.firmware_version,
            generation=generation.value,
            name=name,
            source=source,
        )

        async with self._repository_factory() as repository:
            created = await repository.create(backup)
        logger.info(
            "Created %s backup for %s (mac=%s, id=%s)",
            source,
            device_ip,
            created.device_mac,
            created.id,
        )
        return created

    async def list_backups(
        self, device_mac: str | None = None
    ) -> list[DeviceBackupSummary]:
        """List every backup summary, newest first, optionally filtered by MAC.

        Unbounded; used by callers that want the full set (the CLI listing).
        UI/API list views should use :meth:`list_backups_page` instead.
        """
        async with self._repository_factory() as repository:
            return await repository.list_summaries(device_mac)

    async def list_backups_page(
        self,
        device_mac: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> BackupPage:
        """Return one page of backup summaries plus the total matching count."""
        async with self._repository_factory() as repository:
            items = await repository.list_summaries(device_mac, limit, offset)
            total = await repository.count_summaries(device_mac)
        return BackupPage(items=items, total=total, limit=limit, offset=offset)

    async def get_backup(self, backup_id: int) -> DeviceBackup:
        """Get a full backup including its snapshot.

        Raises:
            BackupNotFoundError: If the backup does not exist (or failed to decrypt).
        """
        async with self._repository_factory() as repository:
            backup = await repository.get(backup_id)
            if backup is None:
                raise BackupNotFoundError(backup_id)
            return backup

    async def delete_backup(self, backup_id: int) -> None:
        """Delete a backup.

        Raises:
            BackupNotFoundError: If the backup does not exist.
        """
        async with self._repository_factory() as repository:
            deleted = await repository.delete(backup_id)
        if not deleted:
            raise BackupNotFoundError(backup_id)
        logger.info("Deleted backup id=%s", backup_id)
