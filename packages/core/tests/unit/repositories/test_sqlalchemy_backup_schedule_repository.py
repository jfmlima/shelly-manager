"""Tests for the SQLAlchemy backup schedule repository."""

import pytest
from core.domain.entities.backup_schedule import BackupSchedule
from core.repositories.models import Base
from core.repositories.sqlalchemy_backup_schedule_repository import (
    SQLAlchemyBackupScheduleRepository,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


def _schedule(name="nightly", **kwargs):
    base = {
        "name": name,
        "interval_seconds": 3600,
        "target_ips": ["192.168.1.10"],
        "target_macs": ["AABBCCDDEEFF"],
        "all_credentialed": False,
        "next_run_at": 1000,
    }
    base.update(kwargs)
    return BackupSchedule(**base)


class TestScheduleRepository:
    async def test_it_round_trips_json_targets(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyBackupScheduleRepository(session)
            created = await repo.create(_schedule())

            fetched = await repo.get(created.id)
            assert fetched is not None
            assert fetched.target_ips == ["192.168.1.10"]
            assert fetched.target_macs == ["AABBCCDDEEFF"]
            assert fetched.interval_seconds == 3600

    async def test_it_get_by_name(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyBackupScheduleRepository(session)
            await repo.create(_schedule(name="weekly"))

            assert (await repo.get_by_name("weekly")) is not None
            assert (await repo.get_by_name("missing")) is None

    async def test_it_list_due_boundary_includes_equal_to_now(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyBackupScheduleRepository(session)
            await repo.create(_schedule(name="due-equal", next_run_at=1000))
            await repo.create(_schedule(name="due-past", next_run_at=500))
            await repo.create(_schedule(name="not-due", next_run_at=2000))
            await repo.create(
                _schedule(name="disabled", next_run_at=100, enabled=False)
            )

            due = await repo.list_due(1000)

            names = {s.name for s in due}
            assert names == {"due-equal", "due-past"}

    async def test_it_set_run_result_advances_row(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyBackupScheduleRepository(session)
            created = await repo.create(_schedule(next_run_at=1000))

            await repo.set_run_result(
                created.id, last_run_at=1000, next_run_at=4600, last_status="ok: 1 ok"
            )

            fetched = await repo.get(created.id)
            assert fetched.last_run_at == 1000
            assert fetched.next_run_at == 4600
            assert fetched.last_status == "ok: 1 ok"

    async def test_it_update_and_delete(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyBackupScheduleRepository(session)
            created = await repo.create(_schedule())

            created.enabled = False
            created.target_ips = ["10.0.0.1"]
            updated = await repo.update(created)
            assert updated.enabled is False
            assert updated.target_ips == ["10.0.0.1"]

            await repo.delete(created.id)
            assert (await repo.get(created.id)) is None
