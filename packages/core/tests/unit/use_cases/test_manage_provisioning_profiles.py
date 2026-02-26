"""Tests for ManageProvisioningProfilesUseCase."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.use_cases.manage_provisioning_profiles import (
    ManageProvisioningProfilesUseCase,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)


class TestManageProvisioningProfilesUseCase:
    @pytest.fixture
    def mock_repository(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_repository):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        return ManageProvisioningProfilesUseCase(
            repository_factory=repository_factory,
        )

    @pytest.fixture
    def sample_profile(self):
        return ProvisioningProfile(
            id=1,
            name="default",
            wifi_ssid="TestNetwork",
            wifi_password="pass123",
            is_default=True,
        )

    async def test_it_lists_profiles(self, use_case, mock_repository, sample_profile):
        mock_repository.list_all.return_value = [sample_profile]

        result = await use_case.list_profiles()

        assert len(result) == 1
        assert result[0].name == "default"
        mock_repository.list_all.assert_called_once()

    async def test_it_gets_profile_by_id(
        self, use_case, mock_repository, sample_profile
    ):
        mock_repository.get.return_value = sample_profile

        result = await use_case.get_profile(1)

        assert result.id == 1
        assert result.name == "default"
        mock_repository.get.assert_called_once_with(1)

    async def test_it_raises_when_profile_not_found(self, use_case, mock_repository):
        mock_repository.get.return_value = None

        with pytest.raises(ProfileNotFoundError):
            await use_case.get_profile(999)

    async def test_it_gets_default_profile(
        self, use_case, mock_repository, sample_profile
    ):
        mock_repository.get_default.return_value = sample_profile

        result = await use_case.get_default_profile()

        assert result is not None
        assert result.is_default is True

    async def test_it_returns_none_when_no_default(self, use_case, mock_repository):
        mock_repository.get_default.return_value = None

        result = await use_case.get_default_profile()

        assert result is None

    async def test_it_creates_profile(self, use_case, mock_repository):
        new_profile = ProvisioningProfile(name="new-profile")
        mock_repository.get_by_name.return_value = None
        mock_repository.list_all.return_value = []
        created = ProvisioningProfile(id=1, name="new-profile", is_default=True)
        mock_repository.create.return_value = created

        result = await use_case.create_profile(new_profile)

        assert result.id == 1
        # First profile should be set as default
        assert new_profile.is_default is True

    async def test_it_raises_when_name_exists(
        self, use_case, mock_repository, sample_profile
    ):
        mock_repository.get_by_name.return_value = sample_profile

        with pytest.raises(ProfileAlreadyExistsError):
            await use_case.create_profile(ProvisioningProfile(name="default"))

    async def test_it_updates_profile(self, use_case, mock_repository, sample_profile):
        mock_repository.get.return_value = sample_profile
        updated = ProvisioningProfile(id=1, name="default", wifi_ssid="NewNetwork")
        mock_repository.update.return_value = updated

        result = await use_case.update_profile(updated)

        assert result.wifi_ssid == "NewNetwork"

    async def test_it_raises_on_update_name_conflict(
        self, use_case, mock_repository, sample_profile
    ):
        mock_repository.get.return_value = sample_profile
        conflict = ProvisioningProfile(id=2, name="other-profile")
        mock_repository.get_by_name.return_value = conflict

        with pytest.raises(ProfileAlreadyExistsError):
            await use_case.update_profile(
                ProvisioningProfile(id=1, name="other-profile")
            )

    async def test_it_deletes_profile(self, use_case, mock_repository, sample_profile):
        mock_repository.get.return_value = sample_profile

        await use_case.delete_profile(1)

        mock_repository.delete.assert_called_once_with(1)

    async def test_it_raises_on_delete_not_found(self, use_case, mock_repository):
        mock_repository.get.return_value = None

        with pytest.raises(ProfileNotFoundError):
            await use_case.delete_profile(999)

    async def test_it_sets_default_profile(
        self, use_case, mock_repository, sample_profile
    ):
        mock_repository.get.return_value = sample_profile

        await use_case.set_default_profile(1)

        mock_repository.set_default.assert_called_once_with(1)

    async def test_it_raises_on_set_default_not_found(self, use_case, mock_repository):
        mock_repository.get.return_value = None

        with pytest.raises(ProfileNotFoundError):
            await use_case.set_default_profile(999)
