import logging
from datetime import UTC, datetime

from core.domain.credentials import Credential
from core.repositories.credentials_repository import CredentialsRepository
from core.repositories.models import Credentials as CredentialsModel
from core.services.encryption_service import EncryptionService
from core.utils.validation import normalize_mac
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SQLAlchemyCredentialsRepository(CredentialsRepository):
    def __init__(self, session: AsyncSession, encryption_service: EncryptionService):
        self.session = session
        self.encryption_service = encryption_service

    async def get(self, mac: str) -> Credential | None:
        mac = normalize_mac(mac)
        stmt = select(CredentialsModel).where(CredentialsModel.mac == mac)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return self._to_domain(record)  # May return None if decryption fails

    async def get_global(self) -> Credential | None:
        return await self.get("*")

    async def set(
        self, mac: str, username: str, password: str, last_seen_ip: str | None = None
    ) -> None:
        mac = normalize_mac(mac)

        # Check if exists to update or create
        stmt = select(CredentialsModel).where(CredentialsModel.mac == mac)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        password_ciphertext = self.encryption_service.encrypt(password)

        if record:
            record.username = username
            record.password_ciphertext = password_ciphertext
            record.rotated_at = int(datetime.now(UTC).timestamp())
            if last_seen_ip:
                record.last_seen_ip = last_seen_ip
        else:
            record = CredentialsModel(
                mac=mac,
                username=username,
                password_ciphertext=password_ciphertext,
                last_seen_ip=last_seen_ip,
            )
            self.session.add(record)

        await self.session.commit()

    async def delete(self, mac: str) -> None:
        mac = normalize_mac(mac)
        stmt = delete(CredentialsModel).where(CredentialsModel.mac == mac)
        await self.session.execute(stmt)
        await self.session.commit()

    async def list_all(self) -> list[Credential | None]:
        """
        List all credentials.

        Returns:
            List of credentials. Entries that failed to decrypt will be None.
        """
        stmt = select(CredentialsModel)
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [self._to_domain(record) for record in records]

    def _to_domain(self, record: CredentialsModel) -> Credential | None:
        """
        Convert database record to domain object.

        Returns:
            Credential object or None if decryption fails (e.g., key changed)
        """
        try:
            password = self.encryption_service.decrypt(record.password_ciphertext)
        except Exception as e:
            logger.error(
                "Failed to decrypt credentials for MAC %s: %s. "
                "This may indicate the encryption key has changed.",
                record.mac,
                e,
            )
            return None

        return Credential(
            mac=record.mac,
            username=record.username,
            password=password,
            last_seen_ip=record.last_seen_ip,
            created_at=record.created_at,
            rotated_at=record.rotated_at,
        )
