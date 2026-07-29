"""Tests for the credentials CLI subgroup."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.credential_commands import credential_commands
from click.testing import CliRunner
from core.domain.credentials import Credential


class TestCredentialCommands:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def _repo(self):
        repo = MagicMock()
        repo.set = AsyncMock()
        repo.delete = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        return repo

    def _obj(self, repo):
        obj = MagicMock()
        obj.console = MagicMock()
        obj.container.initialize_database = AsyncMock()

        @asynccontextmanager
        async def create_repo():
            yield repo

        obj.container.create_credentials_repository = create_repo
        return obj

    def test_it_sets_credentials_with_default_username(self, runner):
        repo = self._repo()

        result = runner.invoke(
            credential_commands,
            ["set", "AA:BB:CC:DD:EE:FF", "secret"],
            obj=self._obj(repo),
        )

        assert result.exit_code == 0
        repo.set.assert_awaited_once_with("AA:BB:CC:DD:EE:FF", "admin", "secret")

    def test_it_sets_credentials_with_custom_username(self, runner):
        repo = self._repo()

        result = runner.invoke(
            credential_commands,
            ["set", "AA:BB:CC:DD:EE:FF", "secret", "--username", "operator"],
            obj=self._obj(repo),
        )

        assert result.exit_code == 0
        repo.set.assert_awaited_once_with("AA:BB:CC:DD:EE:FF", "operator", "secret")

    def test_it_aborts_when_set_fails(self, runner):
        repo = self._repo()
        repo.set.side_effect = Exception("db unavailable")

        result = runner.invoke(
            credential_commands,
            ["set", "AA:BB:CC:DD:EE:FF", "secret"],
            obj=self._obj(repo),
        )

        assert result.exit_code != 0

    def test_it_sets_global_credentials_under_wildcard_mac(self, runner):
        repo = self._repo()

        result = runner.invoke(
            credential_commands,
            ["set-global", "secret"],
            obj=self._obj(repo),
        )

        assert result.exit_code == 0
        repo.set.assert_awaited_once_with("*", "admin", "secret")

    def test_it_lists_stored_credentials(self, runner):
        repo = self._repo()
        repo.list_all.return_value = [
            Credential(
                mac="AA:BB:CC:DD:EE:FF",
                username="admin",
                password="secret",
                last_seen_ip="192.168.1.10",
            )
        ]
        obj = self._obj(repo)

        result = runner.invoke(credential_commands, ["list"], obj=obj)

        assert result.exit_code == 0
        repo.list_all.assert_awaited_once()
        obj.console.print.assert_called_once()

    def test_it_warns_when_no_credentials_stored(self, runner):
        repo = self._repo()
        obj = self._obj(repo)

        result = runner.invoke(credential_commands, ["list"], obj=obj)

        assert result.exit_code == 0
        printed = str(obj.console.print.call_args_list)
        assert "No credentials stored" in printed

    def test_it_skips_credentials_that_could_not_be_decrypted(self, runner):
        repo = self._repo()
        repo.list_all.return_value = [
            None,
            Credential(
                mac="AA:BB:CC:DD:EE:FF",
                username="admin",
                password="secret",
            ),
        ]
        obj = self._obj(repo)

        result = runner.invoke(credential_commands, ["list"], obj=obj)

        assert result.exit_code == 0
        obj.console.print.assert_called_once()

    def test_it_aborts_when_list_fails(self, runner):
        repo = self._repo()
        repo.list_all.side_effect = Exception("db unavailable")

        result = runner.invoke(
            credential_commands,
            ["list"],
            obj=self._obj(repo),
        )

        assert result.exit_code != 0

    def test_it_deletes_credentials(self, runner):
        repo = self._repo()

        result = runner.invoke(
            credential_commands,
            ["delete", "AA:BB:CC:DD:EE:FF"],
            obj=self._obj(repo),
        )

        assert result.exit_code == 0
        repo.delete.assert_awaited_once_with("AA:BB:CC:DD:EE:FF")

    def test_it_aborts_when_delete_fails(self, runner):
        repo = self._repo()
        repo.delete.side_effect = Exception("db unavailable")

        result = runner.invoke(
            credential_commands,
            ["delete", "AA:BB:CC:DD:EE:FF"],
            obj=self._obj(repo),
        )

        assert result.exit_code != 0
