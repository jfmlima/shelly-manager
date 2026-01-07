from abc import ABC, abstractmethod

from core.domain.credentials import Credential


class CredentialsRepository(ABC):
    @abstractmethod
    async def get(self, mac: str) -> Credential | None:
        """Retrieve credentials for a specific MAC address."""
        pass

    @abstractmethod
    async def get_global(self) -> Credential | None:
        """Retrieve global fallback credentials."""
        pass

    @abstractmethod
    async def set(
        self, mac: str, username: str, password: str, last_seen_ip: str | None = None
    ) -> None:
        """Store credentials for a device."""
        pass

    @abstractmethod
    async def delete(self, mac: str) -> None:
        """Delete credentials for a device."""
        pass

    @abstractmethod
    async def list_all(self) -> list[Credential | None]:
        """List all stored credentials. Entries that failed to decrypt will be None."""
        pass
