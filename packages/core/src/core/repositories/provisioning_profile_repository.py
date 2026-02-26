"""Abstract repository for provisioning profiles."""

from abc import ABC, abstractmethod

from core.domain.entities.provisioning_profile import ProvisioningProfile


class ProvisioningProfileRepository(ABC):
    @abstractmethod
    async def get(self, profile_id: int) -> ProvisioningProfile | None:
        """Retrieve a profile by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> ProvisioningProfile | None:
        """Retrieve a profile by name."""
        pass

    @abstractmethod
    async def get_default(self) -> ProvisioningProfile | None:
        """Retrieve the default profile."""
        pass

    @abstractmethod
    async def list_all(self) -> list[ProvisioningProfile]:
        """List all provisioning profiles."""
        pass

    @abstractmethod
    async def create(self, profile: ProvisioningProfile) -> ProvisioningProfile:
        """Create a new profile. Returns the profile with its assigned ID."""
        pass

    @abstractmethod
    async def update(self, profile: ProvisioningProfile) -> ProvisioningProfile:
        """Update an existing profile."""
        pass

    @abstractmethod
    async def delete(self, profile_id: int) -> None:
        """Delete a profile by ID."""
        pass

    @abstractmethod
    async def set_default(self, profile_id: int) -> None:
        """Set a profile as the default, unsetting any previous default."""
        pass
