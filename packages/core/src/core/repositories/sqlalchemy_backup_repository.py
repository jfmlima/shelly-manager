"""SQLAlchemy implementation of the device backup repository."""

import hashlib
import json
import logging

from core.domain.entities.device_backup import DeviceBackup, DeviceBackupSummary
from core.repositories.backup_repository import BackupRepository
from core.repositories.models import DeviceBackups as BackupModel
from core.services.encryption_service import EncryptionService
from core.utils.validation import normalize_mac
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SQLAlchemyBackupRepository(BackupRepository):
    def __init__(self, session: AsyncSession, encryption_service: EncryptionService):
        self.session = session
        self.encryption_service = encryption_service

    async def create(self, backup: DeviceBackup) -> DeviceBackup:
        json_str = json.dumps(backup.snapshot, sort_keys=True)
        sha256 = hashlib.sha256(json_str.encode()).hexdigest()
        size_bytes = len(json_str.encode())

        record = BackupModel(
            device_mac=normalize_mac(backup.device_mac),
            device_ip=backup.device_ip,
            device_name=backup.device_name,
            device_type=backup.device_type,
            firmware_version=backup.firmware_version,
            generation=backup.generation,
            name=backup.name,
            source=backup.source,
            snapshot_ciphertext=self.encryption_service.encrypt(json_str),
            sha256=sha256,
            size_bytes=size_bytes,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        backup.id = record.id
        backup.created_at = record.created_at
        backup.sha256 = sha256
        backup.size_bytes = size_bytes
        return backup

    async def get(self, backup_id: int) -> DeviceBackup | None:
        stmt = select(BackupModel).where(BackupModel.id == backup_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return self._to_domain(record)

    async def list_summaries(
        self, device_mac: str | None = None
    ) -> list[DeviceBackupSummary]:
        stmt = select(BackupModel).order_by(BackupModel.created_at.desc())
        if device_mac is not None:
            stmt = stmt.where(BackupModel.device_mac == normalize_mac(device_mac))
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [self._to_summary(record) for record in records]

    async def delete(self, backup_id: int) -> None:
        stmt = select(BackupModel).where(BackupModel.id == backup_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            await self.session.delete(record)
            await self.session.commit()

    async def count_for_device(
        self, device_mac: str, source: str | None = "scheduled"
    ) -> int:
        mac = normalize_mac(device_mac)
        stmt = (
            select(func.count())
            .select_from(BackupModel)
            .where(BackupModel.device_mac == mac)
        )
        if source is not None:
            stmt = stmt.where(BackupModel.source == source)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def delete_keeping_latest_n(
        self, device_mac: str, n: int, source: str | None = "scheduled"
    ) -> int:
        if n < 1:
            # Refuse to interpret "keep 0" as "delete everything" — that is almost
            # certainly a misconfiguration, not an intent to wipe all snapshots.
            return 0
        mac = normalize_mac(device_mac)
        stmt = select(BackupModel.id).where(BackupModel.device_mac == mac)
        if source is not None:
            stmt = stmt.where(BackupModel.source == source)
        stmt = stmt.order_by(BackupModel.created_at.desc(), BackupModel.id.desc())
        ids = [row[0] for row in (await self.session.execute(stmt)).all()]
        to_delete = ids[n:]
        if not to_delete:
            return 0
        await self.session.execute(
            delete(BackupModel).where(BackupModel.id.in_(to_delete))
        )
        await self.session.commit()
        return len(to_delete)

    async def delete_older_than(
        self, device_mac: str, cutoff_ts: int, source: str | None = "scheduled"
    ) -> int:
        mac = normalize_mac(device_mac)
        conditions = [
            BackupModel.device_mac == mac,
            BackupModel.created_at < cutoff_ts,
        ]
        if source is not None:
            conditions.append(BackupModel.source == source)

        count_stmt = select(func.count()).select_from(BackupModel).where(*conditions)
        count = int((await self.session.execute(count_stmt)).scalar_one())
        if count:
            await self.session.execute(delete(BackupModel).where(*conditions))
            await self.session.commit()
        return count

    def _to_domain(self, record: BackupModel) -> DeviceBackup | None:
        try:
            plaintext = self.encryption_service.decrypt(record.snapshot_ciphertext)
        except Exception as e:
            logger.error("Failed to decrypt backup %s: %s", record.id, e)
            return None

        # Integrity check: the stored digest was computed over this exact
        # plaintext at create time. A mismatch means row/ciphertext corruption
        # or a mix-up, so refuse to hand back a wrong (but decryptable) snapshot.
        if (
            record.sha256
            and hashlib.sha256(plaintext.encode()).hexdigest() != record.sha256
        ):
            logger.error(
                "Backup %s failed integrity check (sha256 mismatch)", record.id
            )
            return None

        snapshot = json.loads(plaintext)

        return DeviceBackup(
            id=record.id,
            device_mac=record.device_mac,
            snapshot=snapshot,
            device_ip=record.device_ip,
            device_name=record.device_name,
            device_type=record.device_type,
            firmware_version=record.firmware_version,
            generation=record.generation,
            name=record.name,
            source=record.source,
            sha256=record.sha256,
            size_bytes=record.size_bytes,
            created_at=record.created_at,
        )

    def _to_summary(self, record: BackupModel) -> DeviceBackupSummary:
        return DeviceBackupSummary(
            id=record.id,
            device_mac=record.device_mac,
            device_ip=record.device_ip,
            device_name=record.device_name,
            device_type=record.device_type,
            firmware_version=record.firmware_version,
            generation=record.generation,
            name=record.name,
            source=record.source,
            sha256=record.sha256,
            size_bytes=record.size_bytes,
            created_at=record.created_at,
        )
