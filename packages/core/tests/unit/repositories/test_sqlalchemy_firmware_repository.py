"""Tests for the SQLAlchemy firmware bundle repository."""

import pytest
from core.domain.entities.firmware_bundle import FirmwareBundle
from core.repositories.models import Base
from core.repositories.sqlalchemy_firmware_repository import (
    SQLAlchemyFirmwareRepository,
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


def _bundle(app_name="Plus2PM", version="1.7.5", **kwargs):
    base = {
        "app_name": app_name,
        "version": version,
        "build_id": f"20250611-100000/{version}-g1234567",
        "file_name": f"{app_name}-{version}.zip",
        "size_bytes": 2048,
        "sha256": "ab" * 32,
    }
    base.update(kwargs)
    return FirmwareBundle(**base)


class TestFirmwareRepository:
    async def test_it_round_trips_a_bundle(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyFirmwareRepository(session)
            created = await repo.create(_bundle())

            assert created.id is not None
            assert created.downloaded_at is not None

            fetched = await repo.get(created.id)
            assert fetched is not None
            assert fetched.app_name == "Plus2PM"
            assert fetched.version == "1.7.5"
            assert fetched.build_id == "20250611-100000/1.7.5-g1234567"
            assert fetched.file_name == "Plus2PM-1.7.5.zip"
            assert fetched.size_bytes == 2048
            assert fetched.sha256 == "ab" * 32

    async def test_it_returns_none_for_a_missing_bundle(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyFirmwareRepository(session)

            assert (await repo.get(12345)) is None

    async def test_it_finds_a_bundle_by_its_full_identity(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyFirmwareRepository(session)
            await repo.create(_bundle(app_name="Plus2PM", version="1.7.5"))
            await repo.create(_bundle(app_name="Mini1PMG4", version="2.0.0"))

            found = await repo.find(
                "Mini1PMG4", "2.0.0", "20250611-100000/2.0.0-g1234567"
            )
            assert found is not None
            assert found.app_name == "Mini1PMG4"
            assert found.version == "2.0.0"

            assert (
                await repo.find("Plus2PM", "9.9.9", "20250611-100000/9.9.9-g1234567")
            ) is None

    async def test_it_misses_a_republished_version_under_a_new_build(
        self, session_factory
    ):
        async with session_factory() as session:
            repo = SQLAlchemyFirmwareRepository(session)
            await repo.create(_bundle(app_name="Plus2PM", version="1.7.5"))

            assert (
                await repo.find("Plus2PM", "1.7.5", "20260101-000000/1.7.5-gdeadbee")
            ) is None

    async def test_it_lists_bundles_newest_first(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyFirmwareRepository(session)
            first = await repo.create(_bundle(version="1.7.3"))
            second = await repo.create(_bundle(version="1.7.4"))
            third = await repo.create(_bundle(version="1.7.5"))

            bundles = await repo.list()

            assert [b.id for b in bundles] == [third.id, second.id, first.id]

    async def test_it_deletes_a_bundle(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyFirmwareRepository(session)
            created = await repo.create(_bundle())

            assert (await repo.delete(created.id)) is True
            assert (await repo.get(created.id)) is None
            assert (await repo.delete(created.id)) is False

    async def test_it_returns_the_existing_row_for_a_duplicate_bundle(
        self, session_factory
    ):
        async with session_factory() as session:
            repo = SQLAlchemyFirmwareRepository(session)
            first = await repo.create(_bundle())

            second = await repo.create(_bundle())

            assert second.id == first.id
            assert len(await repo.list()) == 1
