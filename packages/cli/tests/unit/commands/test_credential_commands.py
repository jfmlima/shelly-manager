"""Tests for the credentials CLI subgroup."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.credential_commands import credential_commands
from cli.exceptions import EXIT_NOT_FOUND, EXIT_VALIDATION
from click.testing import CliRunner
from core.domain.credentials import Credential
from core.use_cases.manage_credentials import CredentialNotFoundError


class TestCredentialCommands:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def use_case(self):
        use_case = MagicMock()
        use_case.set_credential = AsyncMock()
        use_case.delete_credential = AsyncMock()
        use_case.list_credentials = AsyncMock(return_value=[])
        return use_case

    @pytest.fixture
    def obj(self, use_case):
        obj = MagicMock()
        obj.console = MagicMock()
        obj.container.get_credentials_use_case.return_value = use_case
        return obj

    def test_it_sets_credentials_with_default_username(self, runner, obj, use_case):
        result = runner.invoke(
            credential_commands, ["set", "AA:BB:CC:DD:EE:FF", "secret"], obj=obj
        )

        assert result.exit_code == 0
        use_case.set_credential.assert_awaited_once_with(
            "AABBCCDDEEFF", "admin", "secret"
        )

    def test_it_sets_credentials_with_custom_username(self, runner, obj, use_case):
        result = runner.invoke(
            credential_commands,
            ["set", "AA:BB:CC:DD:EE:FF", "secret", "--username", "operator"],
            obj=obj,
        )

        assert result.exit_code == 0
        use_case.set_credential.assert_awaited_once_with(
            "AABBCCDDEEFF", "operator", "secret"
        )

    def test_it_aborts_when_set_fails(self, runner, obj, use_case):
        use_case.set_credential.side_effect = Exception("db unavailable")

        result = runner.invoke(
            credential_commands, ["set", "AA:BB:CC:DD:EE:FF", "secret"], obj=obj
        )

        assert result.exit_code != 0

    def test_it_rejects_an_invalid_mac(self, runner, obj, use_case):
        result = runner.invoke(
            credential_commands, ["set", "not-a-mac", "secret"], obj=obj
        )

        assert result.exit_code == EXIT_VALIDATION
        use_case.set_credential.assert_not_awaited()

    def test_it_sets_global_credentials_under_wildcard_mac(self, runner, obj, use_case):
        result = runner.invoke(credential_commands, ["set-global", "secret"], obj=obj)

        assert result.exit_code == 0
        use_case.set_credential.assert_awaited_once_with("*", "admin", "secret")

    def test_it_lists_stored_credentials(self, runner, obj, use_case):
        use_case.list_credentials.return_value = [
            Credential(
                mac="AA:BB:CC:DD:EE:FF",
                username="admin",
                password="secret",
                last_seen_ip="192.168.1.10",
            )
        ]

        result = runner.invoke(credential_commands, ["list"], obj=obj)

        assert result.exit_code == 0
        obj.console.print.assert_called_once()

    def test_it_warns_when_no_credentials_stored(self, runner, obj):
        result = runner.invoke(credential_commands, ["list"], obj=obj)

        assert result.exit_code == 0
        assert "No credentials stored" in str(obj.console.print.call_args_list)

    def test_it_aborts_when_list_fails(self, runner, obj, use_case):
        use_case.list_credentials.side_effect = Exception("db unavailable")

        result = runner.invoke(credential_commands, ["list"], obj=obj)

        assert result.exit_code != 0

    def test_it_deletes_credentials(self, runner, obj, use_case):
        result = runner.invoke(
            credential_commands, ["delete", "AA:BB:CC:DD:EE:FF"], obj=obj
        )

        assert result.exit_code == 0
        use_case.delete_credential.assert_awaited_once_with("AA:BB:CC:DD:EE:FF")

    def test_it_reports_a_missing_credential_instead_of_success(
        self, runner, obj, use_case
    ):
        use_case.delete_credential.side_effect = CredentialNotFoundError("112233445566")

        result = runner.invoke(
            credential_commands, ["delete", "11:22:33:44:55:66"], obj=obj
        )

        assert result.exit_code == EXIT_NOT_FOUND
        printed = str(obj.console.print.call_args_list)
        assert "Credential not found" in printed
        assert "Credentials deleted" not in printed

    def test_it_aborts_when_delete_fails(self, runner, obj, use_case):
        use_case.delete_credential.side_effect = Exception("db unavailable")

        result = runner.invoke(
            credential_commands, ["delete", "AA:BB:CC:DD:EE:FF"], obj=obj
        )

        assert result.exit_code != 0
