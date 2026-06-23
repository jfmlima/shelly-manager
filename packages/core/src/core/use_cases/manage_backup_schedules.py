"""Use case for managing backup schedules (CRUD plus enable/disable)."""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime

from core.domain.entities.backup_schedule import BackupSchedule
from core.repositories.backup_schedule_repository import BackupScheduleRepository

logger = logging.getLogger(__name__)


def _default_clock() -> int:
    return int(datetime.now(UTC).timestamp())


class ScheduleNotFoundError(Exception):
    """Raised when a backup schedule is not found."""

    def __init__(self, identifier: int | str):
        self.identifier = identifier
        super().__init__(f"Backup schedule not found: {identifier}")


class ScheduleAlreadyExistsError(Exception):
    """Raised when a schedule with the same name already exists."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Backup schedule already exists: {name}")


class ManageBackupSchedulesUseCase:
    """CRUD plus enable/disable for backup schedules."""

    def __init__(
        self,
        repository_factory: Callable[
            [], AbstractAsyncContextManager[BackupScheduleRepository]
        ],
        clock: Callable[[], int] = _default_clock,
    ):
        self._repository_factory = repository_factory
        self._clock = clock

    async def list_schedules(self) -> list[BackupSchedule]:
        """List all schedules, newest first."""
        async with self._repository_factory() as repository:
            return await repository.list_all()

    async def get_schedule(self, schedule_id: int) -> BackupSchedule:
        """Get a schedule by ID.

        Raises:
            ScheduleNotFoundError: If the schedule does not exist.
        """
        async with self._repository_factory() as repository:
            schedule = await repository.get(schedule_id)
            if schedule is None:
                raise ScheduleNotFoundError(schedule_id)
            return schedule

    async def create_schedule(self, schedule: BackupSchedule) -> BackupSchedule:
        """Create a new schedule.

        The first run is one interval out, not immediate, so creating an
        ``all_credentialed`` schedule does not back up the whole fleet at once;
        use run-now for an immediate baseline.

        Raises:
            ScheduleAlreadyExistsError: If a schedule with the same name exists.
        """
        async with self._repository_factory() as repository:
            if await repository.get_by_name(schedule.name) is not None:
                raise ScheduleAlreadyExistsError(schedule.name)
            if schedule.next_run_at is None:
                schedule.next_run_at = self._clock() + schedule.interval_seconds
            created = await repository.create(schedule)
            logger.info("Created backup schedule: %s", schedule.name)
            return created

    async def update_schedule(self, schedule: BackupSchedule) -> BackupSchedule:
        """Update an existing schedule.

        Raises:
            ScheduleNotFoundError: If the schedule does not exist.
            ScheduleAlreadyExistsError: If the new name conflicts with another.
        """
        if schedule.id is None:
            raise ScheduleNotFoundError("unknown (no ID)")

        async with self._repository_factory() as repository:
            existing = await repository.get(schedule.id)
            if existing is None:
                raise ScheduleNotFoundError(schedule.id)

            if schedule.name != existing.name:
                if await repository.get_by_name(schedule.name) is not None:
                    raise ScheduleAlreadyExistsError(schedule.name)

            # A changed cadence restarts the grid from now; otherwise keep the
            # device's place in the existing schedule.
            if schedule.interval_seconds != existing.interval_seconds:
                schedule.next_run_at = self._clock() + schedule.interval_seconds
            elif schedule.next_run_at is None:
                schedule.next_run_at = existing.next_run_at

            updated = await repository.update(schedule)
            logger.info("Updated backup schedule: %s", schedule.name)
            return updated

    async def set_enabled(self, schedule_id: int, enabled: bool) -> BackupSchedule:
        """Enable or disable a schedule.

        Raises:
            ScheduleNotFoundError: If the schedule does not exist.
        """
        async with self._repository_factory() as repository:
            existing = await repository.get(schedule_id)
            if existing is None:
                raise ScheduleNotFoundError(schedule_id)
            existing.enabled = enabled
            updated = await repository.update(existing)
            logger.info(
                "%s backup schedule: %s",
                "Enabled" if enabled else "Disabled",
                existing.name,
            )
            return updated

    async def delete_schedule(self, schedule_id: int) -> None:
        """Delete a schedule.

        Raises:
            ScheduleNotFoundError: If the schedule does not exist.
        """
        async with self._repository_factory() as repository:
            existing = await repository.get(schedule_id)
            if existing is None:
                raise ScheduleNotFoundError(schedule_id)
            await repository.delete(schedule_id)
            logger.info(
                "Deleted backup schedule: %s (id=%s)", existing.name, schedule_id
            )
