"""Use case for managing provisioning profiles."""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.repositories.provisioning_profile_repository import (
    ProvisioningProfileRepository,
)

logger = logging.getLogger(__name__)


class ProfileNotFoundError(Exception):
    """Raised when a provisioning profile is not found."""

    def __init__(self, identifier: str | int):
        self.identifier = identifier
        super().__init__(f"Provisioning profile not found: {identifier}")


class ProfileAlreadyExistsError(Exception):
    """Raised when a profile with the same name already exists."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Provisioning profile already exists: {name}")


class ManageProvisioningProfilesUseCase:
    """CRUD operations for provisioning profiles."""

    def __init__(
        self,
        repository_factory: Callable[
            [], AbstractAsyncContextManager[ProvisioningProfileRepository]
        ],
    ):
        self._repository_factory = repository_factory

    async def list_profiles(self) -> list[ProvisioningProfile]:
        """List all provisioning profiles."""
        async with self._repository_factory() as repository:
            return await repository.list_all()

    async def get_profile(self, profile_id: int) -> ProvisioningProfile:
        """Get a profile by ID.

        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        async with self._repository_factory() as repository:
            profile = await repository.get(profile_id)
            if profile is None:
                raise ProfileNotFoundError(profile_id)
            return profile

    async def get_default_profile(self) -> ProvisioningProfile | None:
        """Get the default profile, or None if no default is set."""
        async with self._repository_factory() as repository:
            return await repository.get_default()

    async def create_profile(self, profile: ProvisioningProfile) -> ProvisioningProfile:
        """Create a new provisioning profile.

        Raises:
            ProfileAlreadyExistsError: If a profile with the same name exists.
        """
        async with self._repository_factory() as repository:
            existing = await repository.get_by_name(profile.name)
            if existing is not None:
                raise ProfileAlreadyExistsError(profile.name)

            # If this is the first profile, make it default
            all_profiles = await repository.list_all()
            if not all_profiles:
                profile.is_default = True

            created = await repository.create(profile)
            logger.info("Created provisioning profile: %s", profile.name)
            return created

    async def update_profile(self, profile: ProvisioningProfile) -> ProvisioningProfile:
        """Update an existing provisioning profile.

        Raises:
            ProfileNotFoundError: If the profile does not exist.
            ProfileAlreadyExistsError: If the new name conflicts with another profile.
        """
        if profile.id is None:
            raise ProfileNotFoundError("unknown (no ID)")

        async with self._repository_factory() as repository:
            existing = await repository.get(profile.id)
            if existing is None:
                raise ProfileNotFoundError(profile.id)

            # Check name uniqueness if name changed
            if profile.name != existing.name:
                name_conflict = await repository.get_by_name(profile.name)
                if name_conflict is not None:
                    raise ProfileAlreadyExistsError(profile.name)

            updated = await repository.update(profile)
            logger.info("Updated provisioning profile: %s", profile.name)
            return updated

    async def delete_profile(self, profile_id: int) -> None:
        """Delete a provisioning profile.

        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        async with self._repository_factory() as repository:
            existing = await repository.get(profile_id)
            if existing is None:
                raise ProfileNotFoundError(profile_id)

            await repository.delete(profile_id)
            logger.info(
                "Deleted provisioning profile: %s (id=%d)",
                existing.name,
                profile_id,
            )

    async def set_default_profile(self, profile_id: int) -> None:
        """Set a profile as the default.

        Raises:
            ProfileNotFoundError: If the profile does not exist.
        """
        async with self._repository_factory() as repository:
            existing = await repository.get(profile_id)
            if existing is None:
                raise ProfileNotFoundError(profile_id)

            await repository.set_default(profile_id)
            logger.info(
                "Set default provisioning profile: %s (id=%d)",
                existing.name,
                profile_id,
            )
