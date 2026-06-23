"""SQLAlchemy implementation of the backup schedule repository."""

import json
import logging
from datetime import UTC, datetime

from core.domain.entities.backup_schedule import BackupSchedule
from core.repositories.backup_schedule_repository import BackupScheduleRepository
from core.repositories.models import BackupSchedules as ScheduleModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SQLAlchemyBackupScheduleRepository(BackupScheduleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, schedule: BackupSchedule) -> BackupSchedule:
        record = ScheduleModel(
            name=schedule.name,
            target_ips=_encode(schedule.target_ips),
            target_macs=_encode(schedule.target_macs),
            all_credentialed=schedule.all_credentialed,
            interval_seconds=schedule.interval_seconds,
            enabled=schedule.enabled,
            retention_keep_last=schedule.retention_keep_last,
            retention_max_age_days=schedule.retention_max_age_days,
            last_run_at=schedule.last_run_at,
            next_run_at=schedule.next_run_at,
            last_status=schedule.last_status,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return self._to_domain(record)

    async def get(self, schedule_id: int) -> BackupSchedule | None:
        stmt = select(ScheduleModel).where(ScheduleModel.id == schedule_id)
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    async def get_by_name(self, name: str) -> BackupSchedule | None:
        stmt = select(ScheduleModel).where(ScheduleModel.name == name)
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(record) if record else None

    async def list_all(self) -> list[BackupSchedule]:
        stmt = select(ScheduleModel).order_by(ScheduleModel.created_at.desc())
        records = (await self.session.execute(stmt)).scalars().all()
        return [self._to_domain(record) for record in records]

    async def list_due(self, now_ts: int) -> list[BackupSchedule]:
        stmt = (
            select(ScheduleModel)
            .where(ScheduleModel.enabled.is_(True))
            .where(ScheduleModel.next_run_at <= now_ts)
            .order_by(ScheduleModel.next_run_at)
        )
        records = (await self.session.execute(stmt)).scalars().all()
        return [self._to_domain(record) for record in records]

    async def update(self, schedule: BackupSchedule) -> BackupSchedule:
        if schedule.id is None:
            raise ValueError("Cannot update a schedule without an ID")

        stmt = select(ScheduleModel).where(ScheduleModel.id == schedule.id)
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        if not record:
            raise ValueError(f"Schedule with ID {schedule.id} not found")

        record.name = schedule.name
        record.target_ips = _encode(schedule.target_ips)
        record.target_macs = _encode(schedule.target_macs)
        record.all_credentialed = schedule.all_credentialed
        record.interval_seconds = schedule.interval_seconds
        record.enabled = schedule.enabled
        record.retention_keep_last = schedule.retention_keep_last
        record.retention_max_age_days = schedule.retention_max_age_days
        if schedule.next_run_at is not None:
            record.next_run_at = schedule.next_run_at
        record.updated_at = int(datetime.now(UTC).timestamp())

        await self.session.commit()
        await self.session.refresh(record)
        return self._to_domain(record)

    async def set_run_result(
        self,
        schedule_id: int,
        last_run_at: int,
        next_run_at: int,
        last_status: str | None,
    ) -> None:
        stmt = select(ScheduleModel).where(ScheduleModel.id == schedule_id)
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        if not record:
            return
        record.last_run_at = last_run_at
        record.next_run_at = next_run_at
        record.last_status = last_status
        await self.session.commit()

    async def delete(self, schedule_id: int) -> None:
        stmt = select(ScheduleModel).where(ScheduleModel.id == schedule_id)
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        if record:
            await self.session.delete(record)
            await self.session.commit()

    def _to_domain(self, record: ScheduleModel) -> BackupSchedule:
        return BackupSchedule(
            id=record.id,
            name=record.name,
            interval_seconds=record.interval_seconds,
            target_ips=_decode(record.target_ips),
            target_macs=_decode(record.target_macs),
            all_credentialed=record.all_credentialed,
            enabled=record.enabled,
            retention_keep_last=record.retention_keep_last,
            retention_max_age_days=record.retention_max_age_days,
            last_run_at=record.last_run_at,
            next_run_at=record.next_run_at,
            last_status=record.last_status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


def _encode(values: list[str]) -> str:
    return json.dumps(list(values))


def _decode(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
    except (ValueError, TypeError):
        logger.warning("Could not decode schedule target list: %r", raw)
        return []
    if not isinstance(decoded, list):
        return []
    return [str(item) for item in decoded]
