import pytest
from core.domain.entities.device_backup import DeviceBackup
from core.repositories.models import Base
from core.repositories.sqlalchemy_backup_repository import SQLAlchemyBackupRepository
from core.services.encryption_service import EncryptionService
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


def _backup(mac="AABBCCDDEEFF", name="b1"):
    return DeviceBackup(
        device_mac=mac,
        snapshot={"components": {"switch:0": {"type": "switch", "config": {"x": 1}}}},
        device_ip="192.168.1.100",
        device_name="Test",
        generation="gen2",
        name=name,
    )


class TestSQLAlchemyBackupRepository:
    async def test_it_round_trips_snapshot_with_encryption(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyBackupRepository(session, EncryptionService())
            created = await repo.create(_backup())

            assert created.id is not None
            assert created.sha256 is not None
            assert created.size_bytes > 0

            fetched = await repo.get(created.id)
            assert fetched is not None
            assert fetched.snapshot == {
                "components": {"switch:0": {"type": "switch", "config": {"x": 1}}}
            }
            assert fetched.device_mac == "AABBCCDDEEFF"

    async def test_it_stores_snapshot_encrypted(self, session_factory):
        from core.repositories.models import DeviceBackups
        from sqlalchemy import select

        async with session_factory() as session:
            repo = SQLAlchemyBackupRepository(session, EncryptionService())
            await repo.create(_backup())

            row = (await session.execute(select(DeviceBackups))).scalar_one()
            assert "switch:0" not in row.snapshot_ciphertext

    async def test_list_summaries_omits_snapshot_and_filters_by_mac(
        self, session_factory
    ):
        async with session_factory() as session:
            repo = SQLAlchemyBackupRepository(session, EncryptionService())
            await repo.create(_backup(mac="AABBCCDDEEFF", name="a"))
            await repo.create(_backup(mac="112233445566", name="b"))

            all_summaries = await repo.list_summaries()
            assert len(all_summaries) == 2

            filtered = await repo.list_summaries("AA:BB:CC:DD:EE:FF")
            assert len(filtered) == 1
            assert filtered[0].device_mac == "AABBCCDDEEFF"
            # summary type carries no snapshot attribute
            assert not hasattr(filtered[0], "snapshot")

    async def test_it_deletes_a_backup(self, session_factory):
        async with session_factory() as session:
            repo = SQLAlchemyBackupRepository(session, EncryptionService())
            created = await repo.create(_backup())

            await repo.delete(created.id)

            assert await repo.get(created.id) is None

    async def test_it_rejects_a_tampered_backup_on_read(self, session_factory):
        from core.repositories.models import DeviceBackups
        from sqlalchemy import select

        async with session_factory() as session:
            repo = SQLAlchemyBackupRepository(session, EncryptionService())
            created = await repo.create(_backup())

            # Corrupt the stored digest so it no longer matches the plaintext.
            row = (
                await session.execute(
                    select(DeviceBackups).where(DeviceBackups.id == created.id)
                )
            ).scalar_one()
            row.sha256 = "deadbeef"
            await session.commit()

            assert await repo.get(created.id) is None
