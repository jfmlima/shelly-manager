"""Tests for the backup-schedule management use case."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.backup_schedule import BackupSchedule
from core.use_cases.manage_backup_schedules import (
    ManageBackupSchedulesUseCase,
    ScheduleAlreadyExistsError,
    ScheduleNotFoundError,
)

NOW = 500_000


def _factory(repo):
    @asynccontextmanager
    async def factory():
        yield repo

    return factory


def _use_case(repo, clock=NOW):
    return ManageBackupSchedulesUseCase(
        repository_factory=_factory(repo), clock=lambda: clock
    )


def _schedule(**kwargs):
    base = {"name": "nightly", "interval_seconds": 3600, "target_ips": ["192.168.1.10"]}
    base.update(kwargs)
    return BackupSchedule(**base)


class TestCreate:
    async def test_it_sets_next_run_one_interval_out(self):
        repo = AsyncMock(
            get_by_name=AsyncMock(return_value=None),
            create=AsyncMock(side_effect=lambda s: s),
        )
        use_case = _use_case(repo)

        created = await use_case.create_schedule(_schedule(interval_seconds=3600))

        assert created.next_run_at == NOW + 3600

    async def test_it_rejects_duplicate_name(self):
        repo = AsyncMock(get_by_name=AsyncMock(return_value=_schedule(id=1)))
        use_case = _use_case(repo)

        with pytest.raises(ScheduleAlreadyExistsError):
            await use_case.create_schedule(_schedule())


class TestUpdate:
    async def test_it_recomputes_next_run_when_interval_changes(self):
        existing = _schedule(id=1, interval_seconds=3600, next_run_at=NOW + 100)
        repo = AsyncMock(
            get=AsyncMock(return_value=existing),
            get_by_name=AsyncMock(return_value=None),
            update=AsyncMock(side_effect=lambda s: s),
        )
        use_case = _use_case(repo)

        incoming = _schedule(id=1, interval_seconds=7200, next_run_at=NOW + 100)
        updated = await use_case.update_schedule(incoming)

        assert updated.next_run_at == NOW + 7200

    async def test_it_keeps_next_run_when_interval_unchanged(self):
        existing = _schedule(id=1, interval_seconds=3600, next_run_at=NOW + 100)
        repo = AsyncMock(
            get=AsyncMock(return_value=existing),
            get_by_name=AsyncMock(return_value=None),
            update=AsyncMock(side_effect=lambda s: s),
        )
        use_case = _use_case(repo)

        incoming = _schedule(id=1, interval_seconds=3600, next_run_at=None)
        updated = await use_case.update_schedule(incoming)

        assert updated.next_run_at == NOW + 100

    async def test_it_missing_raises(self):
        repo = AsyncMock(get=AsyncMock(return_value=None))
        use_case = _use_case(repo)

        with pytest.raises(ScheduleNotFoundError):
            await use_case.update_schedule(_schedule(id=99))


class TestEnableDisableDelete:
    async def test_it_set_enabled_toggles(self):
        existing = _schedule(id=1, enabled=True)
        repo = AsyncMock(
            get=AsyncMock(return_value=existing),
            update=AsyncMock(side_effect=lambda s: s),
        )
        use_case = _use_case(repo)

        updated = await use_case.set_enabled(1, False)

        assert updated.enabled is False

    async def test_it_delete_missing_raises(self):
        repo = AsyncMock(get=AsyncMock(return_value=None))
        use_case = _use_case(repo)

        with pytest.raises(ScheduleNotFoundError):
            await use_case.delete_schedule(99)
