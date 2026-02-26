"""SQLAlchemy implementation of the provisioning profile repository."""

import logging
from datetime import UTC, datetime

from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.repositories.models import ProvisioningProfiles as ProfileModel
from core.repositories.provisioning_profile_repository import (
    ProvisioningProfileRepository,
)
from core.services.encryption_service import EncryptionService
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SQLAlchemyProvisioningProfileRepository(ProvisioningProfileRepository):
    def __init__(self, session: AsyncSession, encryption_service: EncryptionService):
        self.session = session
        self.encryption_service = encryption_service

    async def get(self, profile_id: int) -> ProvisioningProfile | None:
        stmt = select(ProfileModel).where(ProfileModel.id == profile_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return self._to_domain(record)

    async def get_by_name(self, name: str) -> ProvisioningProfile | None:
        stmt = select(ProfileModel).where(ProfileModel.name == name)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return self._to_domain(record)

    async def get_default(self) -> ProvisioningProfile | None:
        stmt = select(ProfileModel).where(ProfileModel.is_default.is_(True))
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return self._to_domain(record)

    async def list_all(self) -> list[ProvisioningProfile]:
        stmt = select(ProfileModel).order_by(ProfileModel.name)
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        profiles = []
        for record in records:
            profile = self._to_domain(record)
            if profile is not None:
                profiles.append(profile)
        return profiles

    async def create(self, profile: ProvisioningProfile) -> ProvisioningProfile:
        record = ProfileModel(
            name=profile.name,
            wifi_ssid=profile.wifi_ssid,
            wifi_password_ciphertext=self._encrypt_optional(profile.wifi_password),
            mqtt_enabled=profile.mqtt_enabled,
            mqtt_server=profile.mqtt_server,
            mqtt_user=profile.mqtt_user,
            mqtt_password_ciphertext=self._encrypt_optional(profile.mqtt_password),
            mqtt_topic_prefix_template=profile.mqtt_topic_prefix_template,
            auth_password_ciphertext=self._encrypt_optional(profile.auth_password),
            device_name_template=profile.device_name_template,
            timezone=profile.timezone,
            cloud_enabled=profile.cloud_enabled,
            is_default=profile.is_default,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return self._to_domain(record)  # type: ignore[return-value]

    async def update(self, profile: ProvisioningProfile) -> ProvisioningProfile:
        if profile.id is None:
            raise ValueError("Cannot update a profile without an ID")

        stmt = select(ProfileModel).where(ProfileModel.id == profile.id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise ValueError(f"Profile with ID {profile.id} not found")

        record.name = profile.name
        record.wifi_ssid = profile.wifi_ssid
        record.wifi_password_ciphertext = self._encrypt_optional(profile.wifi_password)
        record.mqtt_enabled = profile.mqtt_enabled
        record.mqtt_server = profile.mqtt_server
        record.mqtt_user = profile.mqtt_user
        record.mqtt_password_ciphertext = self._encrypt_optional(profile.mqtt_password)
        record.mqtt_topic_prefix_template = profile.mqtt_topic_prefix_template
        record.auth_password_ciphertext = self._encrypt_optional(profile.auth_password)
        record.device_name_template = profile.device_name_template
        record.timezone = profile.timezone
        record.cloud_enabled = profile.cloud_enabled
        record.is_default = profile.is_default
        record.updated_at = int(datetime.now(UTC).timestamp())

        await self.session.commit()
        return self._to_domain(record)  # type: ignore[return-value]

    async def delete(self, profile_id: int) -> None:
        stmt = select(ProfileModel).where(ProfileModel.id == profile_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            await self.session.delete(record)
            await self.session.commit()

    async def set_default(self, profile_id: int) -> None:
        # Unset all defaults
        stmt = (
            update(ProfileModel)
            .where(ProfileModel.is_default.is_(True))
            .values(is_default=False)
        )
        await self.session.execute(stmt)

        # Set the new default
        stmt = (
            update(ProfileModel)
            .where(ProfileModel.id == profile_id)
            .values(is_default=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    def _encrypt_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        return self.encryption_service.encrypt(value)

    def _decrypt_optional(self, ciphertext: str | None) -> str | None:
        if ciphertext is None:
            return None
        try:
            return self.encryption_service.decrypt(ciphertext)
        except Exception as e:
            logger.error("Failed to decrypt field: %s", e)
            return None

    def _to_domain(self, record: ProfileModel) -> ProvisioningProfile | None:
        try:
            return ProvisioningProfile(
                id=record.id,
                name=record.name,
                wifi_ssid=record.wifi_ssid,
                wifi_password=self._decrypt_optional(record.wifi_password_ciphertext),
                mqtt_enabled=record.mqtt_enabled,
                mqtt_server=record.mqtt_server,
                mqtt_user=record.mqtt_user,
                mqtt_password=self._decrypt_optional(record.mqtt_password_ciphertext),
                mqtt_topic_prefix_template=record.mqtt_topic_prefix_template,
                auth_password=self._decrypt_optional(record.auth_password_ciphertext),
                device_name_template=record.device_name_template,
                timezone=record.timezone,
                cloud_enabled=record.cloud_enabled,
                is_default=record.is_default,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
        except Exception as e:
            logger.error(
                "Failed to convert profile '%s' to domain object: %s",
                record.name,
                e,
            )
            return None
