"""Use case for capturing and managing device configuration backups."""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from core.domain.entities.device_backup import (
    BackupPage,
    DeviceBackup,
    DeviceBackupSummary,
)
from core.domain.entities.exceptions import DeviceNotFoundError
from core.gateways.device import DeviceGateway
from core.repositories.backup_repository import BackupRepository
from core.use_cases.bulk_operations import BulkOperationsUseCase

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

    Reuses ``BulkOperationsUseCase.export_bulk_config`` so the stored snapshot is
    identical in shape to the bulk-export endpoint output for one device.
    """

    def __init__(
        self,
        device_gateway: DeviceGateway,
        bulk_operations: BulkOperationsUseCase,
        repository_factory: Callable[[], AbstractAsyncContextManager[BackupRepository]],
    ):
        self._device_gateway = device_gateway
        self._bulk_operations = bulk_operations
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
            | {"schedules"}
        )
        export = await self._bulk_operations.export_bulk_config(
            [device_ip], component_types
        )
        devices = export.get("devices", {})
        if device_ip not in devices:
            # The device dropped during export's own status fetch. Never persist
            # an empty snapshot that would masquerade as a successful backup.
            raise DeviceNotFoundError(device_ip)
        device_block = devices[device_ip]
        components = device_block.get("components") or {}
        if not any(_has_restorable_payload(entry) for entry in components.values()):
            raise BackupError(
                f"No restorable configuration captured for {device_ip}; "
                "backup aborted"
            )

        mac = status.mac_address or device_block.get("device_info", {}).get(
            "mac_address"
        )
        if not mac:
            raise BackupError(
                f"Could not determine MAC address for device {device_ip}; "
                "backup aborted"
            )

        # Generation comes from the device's explicit `gen` field (Gen2+ RPC) or
        # the legacy gateway's gen=1 stamp — never inferred from a missing field.
        if status.gen == 1:
            generation = "gen1"
        elif status.gen is not None and status.gen >= 2:
            generation = "gen2"
        else:
            raise BackupError(
                f"Could not determine device generation for {device_ip}; "
                "backup aborted"
            )

        backup = DeviceBackup(
            device_mac=mac,
            snapshot=device_block,
            device_ip=device_ip,
            device_name=status.device_name,
            device_type=status.device_type,
            firmware_version=status.firmware_version,
            generation=generation,
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

        Unbounded — used by callers that want the full set (the CLI listing).
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
            summaries = await repository.list_summaries()
            if not any(summary.id == backup_id for summary in summaries):
                raise BackupNotFoundError(backup_id)
            await repository.delete(backup_id)
        logger.info("Deleted backup id=%s", backup_id)


def _has_restorable_payload(entry: dict[str, Any]) -> bool:
    """True if a captured component carries something a restore could apply.

    Scripts are only restorable when their code was actually fetched
    (``GetConfig`` succeeding is not enough — restore re-pushes ``code.data``).
    """
    if entry.get("type") == "script":
        code = entry.get("code")
        # Presence + type, not truthiness: an empty script body ("") is valid.
        return isinstance(code, dict) and isinstance(code.get("data"), str)
    return bool(entry.get("success") and entry.get("config") is not None)
