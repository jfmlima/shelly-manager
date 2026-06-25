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
        self,
        device_mac: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[DeviceBackupSummary]:
        """List backup summaries (no snapshot), newest first.

        Optionally filtered by device MAC. When ``limit`` is ``None`` every
        match is returned; otherwise the result is windowed by ``limit``/
        ``offset`` for pagination.
        """
        pass

    @abstractmethod
    async def count_summaries(self, device_mac: str | None = None) -> int:
        """Count stored backups, optionally filtered by device MAC.

        Counts every source (manual and scheduled) — this is the total a
        paginated list view paginates over, not a retention scope.
        """
        pass

    @abstractmethod
    async def delete(self, backup_id: int) -> None:
        """Delete a backup by ID."""
        pass

    @abstractmethod
    async def count_for_device(
        self, device_mac: str, source: str | None = "scheduled"
    ) -> int:
        """Count stored backups for a device. ``source=None`` counts every source."""
        pass

    @abstractmethod
    async def delete_keeping_latest_n(
        self, device_mac: str, n: int, source: str | None = "scheduled"
    ) -> int:
        """Delete all but the newest ``n`` backups for a device. Returns count deleted.

        Defaults to pruning only scheduled backups so a retention policy never
        deletes a user's manually captured snapshot.
        """
        pass

    @abstractmethod
    async def delete_older_than(
        self, device_mac: str, cutoff_ts: int, source: str | None = "scheduled"
    ) -> int:
        """Delete backups older than ``cutoff_ts``. Returns count deleted."""
        pass
