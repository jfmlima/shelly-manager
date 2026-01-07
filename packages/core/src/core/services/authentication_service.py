import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from core.domain.credentials import Credential
from core.repositories.credentials_repository import CredentialsRepository
from core.utils.validation import normalize_mac

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Service for resolving device authentication credentials.

    Uses a repository factory to obtain fresh repository instances for each operation,
    ensuring proper session lifecycle while respecting dependency injection principles.
    """

    def __init__(
        self,
        repository_factory: Callable[
            [], AbstractAsyncContextManager[CredentialsRepository]
        ],
    ):
        """
        Args:
            repository_factory: Async context manager factory that provides repository instances
        """
        self.repository_factory = repository_factory

    async def resolve_credentials(self, mac: str) -> Credential | None:
        """
        Resolve credentials for a given MAC address.

        Resolution order:
        1. Device-specific credential
        2. Global fallback credential (mac='*')
        3. None
        """
        mac = normalize_mac(mac)

        try:
            async with self.repository_factory() as repository:
                creds = await repository.get(mac)
                if creds:
                    return creds

                return await repository.get_global()
        except Exception as e:
            logger.error("Failed to resolve credentials for MAC %s: %s", mac, e)
            return None
