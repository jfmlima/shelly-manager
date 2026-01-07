from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.domain.credentials import Credential
from core.use_cases.manage_credentials import (
    CredentialNotFoundError,
    ManageCredentialsUseCase,
)


class TestManageCredentialsUseCase:
    @pytest.fixture
    def mock_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_callback(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_repository, mock_callback):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        return ManageCredentialsUseCase(
            repository_factory=repository_factory,
            on_credential_changed=mock_callback,
        )

    @pytest.fixture
    def sample_credential(self):
        return Credential(
            mac="AABBCCDDEEFF",
            username="admin",
            password="secret123",
            last_seen_ip="192.168.1.100",
        )

    async def test_it_lists_all_credentials(
        self, use_case, mock_repository, sample_credential
    ):
        mock_repository.list_all.return_value = [sample_credential]

        result = await use_case.list_credentials()

        assert len(result) == 1
        assert result[0].mac == "AABBCCDDEEFF"
        mock_repository.list_all.assert_called_once()

    async def test_it_filters_out_none_values_when_listing(
        self, use_case, mock_repository, sample_credential
    ):
        # Simulate decryption failures returning None
        mock_repository.list_all.return_value = [
            sample_credential,
            None,
            sample_credential,
        ]

        result = await use_case.list_credentials()

        assert len(result) == 2
        assert all(c is not None for c in result)

    async def test_it_returns_empty_list_when_no_credentials(
        self, use_case, mock_repository
    ):
        mock_repository.list_all.return_value = []

        result = await use_case.list_credentials()

        assert result == []

    async def test_it_gets_credential_by_mac(
        self, use_case, mock_repository, sample_credential
    ):
        mock_repository.get.return_value = sample_credential

        result = await use_case.get_credential("AA:BB:CC:DD:EE:FF")

        assert result is not None
        assert result.mac == "AABBCCDDEEFF"
        # MAC should be normalized when calling repository
        mock_repository.get.assert_called_once_with("AABBCCDDEEFF")

    async def test_it_returns_none_when_credential_not_found(
        self, use_case, mock_repository
    ):
        mock_repository.get.return_value = None

        result = await use_case.get_credential("AABBCCDDEEFF")

        assert result is None

    async def test_it_sets_new_credential(
        self, use_case, mock_repository, mock_callback
    ):
        mock_repository.set.return_value = None

        result = await use_case.set_credential(
            mac="AA:BB:CC:DD:EE:FF",
            username="admin",
            password="newpassword",
        )

        assert result.mac == "AABBCCDDEEFF"
        assert result.username == "admin"
        mock_repository.set.assert_called_once_with(
            mac="AABBCCDDEEFF",
            username="admin",
            password="newpassword",
            last_seen_ip=None,
        )
        mock_callback.assert_called_once_with("AABBCCDDEEFF")

    async def test_it_sets_credential_with_last_seen_ip(
        self, use_case, mock_repository, mock_callback
    ):
        mock_repository.set.return_value = None

        result = await use_case.set_credential(
            mac="AABBCCDDEEFF",
            username="admin",
            password="secret",
            last_seen_ip="192.168.1.50",
        )

        assert result.last_seen_ip == "192.168.1.50"
        mock_repository.set.assert_called_once_with(
            mac="AABBCCDDEEFF",
            username="admin",
            password="secret",
            last_seen_ip="192.168.1.50",
        )

    async def test_it_sets_global_credential(
        self, use_case, mock_repository, mock_callback
    ):
        mock_repository.set.return_value = None

        result = await use_case.set_credential(
            mac="*",
            username="admin",
            password="globalpass",
        )

        assert result.mac == "*"
        mock_repository.set.assert_called_once_with(
            mac="*",
            username="admin",
            password="globalpass",
            last_seen_ip=None,
        )
        mock_callback.assert_called_once_with("*")

    async def test_it_deletes_existing_credential(
        self, use_case, mock_repository, mock_callback, sample_credential
    ):
        mock_repository.get.return_value = sample_credential
        mock_repository.delete.return_value = None

        await use_case.delete_credential("AA:BB:CC:DD:EE:FF")

        mock_repository.get.assert_called_once_with("AABBCCDDEEFF")
        mock_repository.delete.assert_called_once_with("AABBCCDDEEFF")
        mock_callback.assert_called_once_with("AABBCCDDEEFF")

    async def test_it_raises_error_when_deleting_non_existent_credential(
        self, use_case, mock_repository, mock_callback
    ):
        mock_repository.get.return_value = None

        with pytest.raises(CredentialNotFoundError) as exc_info:
            await use_case.delete_credential("AABBCCDDEEFF")

        assert "AABBCCDDEEFF" in str(exc_info.value)
        mock_repository.delete.assert_not_called()
        mock_callback.assert_not_called()

    async def test_it_normalizes_mac_address_with_colons(
        self, use_case, mock_repository
    ):
        mock_repository.get.return_value = None

        await use_case.get_credential("aa:bb:cc:dd:ee:ff")

        mock_repository.get.assert_called_once_with("AABBCCDDEEFF")

    async def test_it_normalizes_mac_address_with_dashes(
        self, use_case, mock_repository
    ):
        mock_repository.get.return_value = None

        await use_case.get_credential("AA-BB-CC-DD-EE-FF")

        mock_repository.get.assert_called_once_with("AABBCCDDEEFF")

    async def test_it_works_without_callback(self, mock_repository):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        use_case = ManageCredentialsUseCase(
            repository_factory=repository_factory,
            on_credential_changed=None,
        )
        mock_repository.set.return_value = None

        # Should not raise even without callback
        result = await use_case.set_credential(
            mac="AABBCCDDEEFF",
            username="admin",
            password="secret",
        )

        assert result.mac == "AABBCCDDEEFF"


class TestCredentialNotFoundError:
    def test_it_includes_mac_in_message(self):
        error = CredentialNotFoundError("AABBCCDDEEFF")

        assert "AABBCCDDEEFF" in str(error)
        assert error.mac == "AABBCCDDEEFF"
