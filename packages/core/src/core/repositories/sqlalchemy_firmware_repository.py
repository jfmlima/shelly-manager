"""SQLAlchemy implementation of the firmware bundle repository."""

from core.domain.entities.firmware_bundle import FirmwareBundle
from core.repositories.firmware_repository import FirmwareRepository
from core.repositories.models import FirmwareBundles as FirmwareBundleModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyFirmwareRepository(FirmwareRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, bundle: FirmwareBundle) -> FirmwareBundle:
        record = FirmwareBundleModel(
            app_name=bundle.app_name,
            version=bundle.version,
            build_id=bundle.build_id,
            file_name=bundle.file_name,
            size_bytes=bundle.size_bytes,
            sha256=bundle.sha256,
        )
        self.session.add(record)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            existing = await self.find(bundle.app_name, bundle.version, bundle.build_id)
            if existing is not None:
                return existing
            raise
        await self.session.refresh(record)

        bundle.id = record.id
        bundle.downloaded_at = record.downloaded_at
        return bundle

    async def get(self, bundle_id: int) -> FirmwareBundle | None:
        stmt = select(FirmwareBundleModel).where(FirmwareBundleModel.id == bundle_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._to_domain(record)

    async def find(
        self, app_name: str, version: str, build_id: str
    ) -> FirmwareBundle | None:
        stmt = select(FirmwareBundleModel).where(
            FirmwareBundleModel.app_name == app_name,
            FirmwareBundleModel.version == version,
            FirmwareBundleModel.build_id == build_id,
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._to_domain(record)

    async def list(self) -> list[FirmwareBundle]:
        stmt = select(FirmwareBundleModel).order_by(
            FirmwareBundleModel.downloaded_at.desc(), FirmwareBundleModel.id.desc()
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(record) for record in result.scalars().all()]

    async def delete(self, bundle_id: int) -> bool:
        stmt = select(FirmwareBundleModel).where(FirmwareBundleModel.id == bundle_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return False
        await self.session.delete(record)
        await self.session.commit()
        return True

    def _to_domain(self, record: FirmwareBundleModel) -> FirmwareBundle:
        return FirmwareBundle(
            id=record.id,
            app_name=record.app_name,
            version=record.version,
            build_id=record.build_id,
            file_name=record.file_name,
            size_bytes=record.size_bytes,
            sha256=record.sha256,
            downloaded_at=record.downloaded_at,
        )
