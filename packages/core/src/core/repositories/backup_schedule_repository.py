"""Abstract repository for automated backup schedules."""

from abc import ABC, abstractmethod

from core.domain.entities.backup_schedule import BackupSchedule


class BackupScheduleRepository(ABC):
    @abstractmethod
    async def create(self, schedule: BackupSchedule) -> BackupSchedule:
        """Persist a schedule. Returns it with the assigned ID."""
        pass

    @abstractmethod
    async def get(self, schedule_id: int) -> BackupSchedule | None:
        """Retrieve a schedule by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> BackupSchedule | None:
        """Retrieve a schedule by its unique name."""
        pass

    @abstractmethod
    async def list_all(self) -> list[BackupSchedule]:
        """List all schedules, newest first."""
        pass

    @abstractmethod
    async def list_due(self, now_ts: int) -> list[BackupSchedule]:
        """List enabled schedules whose next_run_at is at or before now_ts."""
        pass

    @abstractmethod
    async def update(self, schedule: BackupSchedule) -> BackupSchedule:
        """Update an existing schedule."""
        pass

    @abstractmethod
    async def set_run_result(
        self,
        schedule_id: int,
        last_run_at: int,
        next_run_at: int,
        last_status: str | None,
    ) -> None:
        """Record the outcome of a run and advance next_run_at.

        A narrow single-row write so a long batch never holds a wide transaction.
        """
        pass

    @abstractmethod
    async def delete(self, schedule_id: int) -> None:
        """Delete a schedule by ID."""
        pass
