"""
Credential management use case.
"""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from core.domain.credentials import Credential
from core.repositories.credentials_repository import CredentialsRepository
from core.utils.validation import normalize_mac

logger = logging.getLogger(__name__)


class CredentialNotFoundError(Exception):
    """Raised when a credential is not found."""

    def __init__(self, mac: str):
        self.mac = mac
        super().__init__(f"Credential not found for MAC: {mac}")


class ManageCredentialsUseCase:
    """
    Use case for managing device credentials.

    Handles CRUD operations for device authentication credentials,
    including cache invalidation when credentials are updated.
    """

    def __init__(
        self,
        repository_factory: Callable[
            [], AbstractAsyncContextManager[CredentialsRepository]
        ],
        on_credential_changed: Callable[[str], None] | None = None,
    ):
        """
        Args:
            repository_factory: Factory that creates credential repository instances
            on_credential_changed: Optional callback invoked when credentials change
                                   (e.g., to invalidate auth caches)
        """
        self._repository_factory = repository_factory
        self._on_credential_changed = on_credential_changed

    async def list_credentials(self) -> list[Credential]:
        """
        List all stored credentials.

        Returns:
            List of credentials (excluding any that failed to decrypt)
        """
        async with self._repository_factory() as repository:
            all_creds = await repository.list_all()
            # Filter out None values (decryption failures)
            return [c for c in all_creds if c is not None]

    async def get_credential(self, mac: str) -> Credential | None:
        """
        Get credential for a specific device.

        Args:
            mac: Device MAC address

        Returns:
            Credential or None if not found
        """
        normalized = normalize_mac(mac)
        async with self._repository_factory() as repository:
            return await repository.get(normalized)

    async def set_credential(
        self,
        mac: str,
        username: str,
        password: str,
        last_seen_ip: str | None = None,
    ) -> Credential:
        """
        Set or update credentials for a device.

        Args:
            mac: Device MAC address (or '*' for global fallback)
            username: Authentication username
            password: Authentication password
            last_seen_ip: Optional last known IP address

        Returns:
            The created/updated credential
        """
        normalized = normalize_mac(mac)

        async with self._repository_factory() as repository:
            await repository.set(
                mac=normalized,
                username=username,
                password=password,
                last_seen_ip=last_seen_ip,
            )

        # Notify listeners about credential change (e.g., to invalidate caches)
        if self._on_credential_changed:
            self._on_credential_changed(normalized)

        logger.info("Credential set for MAC: %s", normalized)

        return Credential(
            mac=normalized,
            username=username,
            password=password,
            last_seen_ip=last_seen_ip,
        )

    async def delete_credential(self, mac: str) -> None:
        """
        Delete credentials for a device.

        Args:
            mac: Device MAC address

        Raises:
            CredentialNotFoundError: If no credential exists for the MAC
        """
        normalized = normalize_mac(mac)

        async with self._repository_factory() as repository:
            existing = await repository.get(normalized)
            if not existing:
                raise CredentialNotFoundError(normalized)

            await repository.delete(normalized)

        # Notify listeners about credential change
        if self._on_credential_changed:
            self._on_credential_changed(normalized)

        logger.info("Credential deleted for MAC: %s", normalized)
