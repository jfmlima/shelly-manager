"""Abstract repository for device configuration backups."""

from abc import ABC, abstractmethod

from core.domain.entities.device_backup import DeviceBackup, DeviceBackupSummary


class BackupRepository(ABC):
    @abstractmethod
    async def create(self, backup: DeviceBackup) -> DeviceBackup:
        """Persist a backup. Returns the backup with its assigned ID."""
        pass

    @abstractmethod
    async def get(self, backup_id: int) -> DeviceBackup | None:
        """Retrieve a backup by ID, decrypting its snapshot."""
        pass

    @abstractmethod
    async def list_summaries(
        self, device_mac: str | None = None
    ) -> list[DeviceBackupSummary]:
        """List backup summaries (no snapshot), newest first.

        Optionally filtered by device MAC.
        """
        pass

    @abstractmethod
    async def delete(self, backup_id: int) -> None:
        """Delete a backup by ID."""
        pass
