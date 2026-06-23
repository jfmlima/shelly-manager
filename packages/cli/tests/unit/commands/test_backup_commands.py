"""Tests for backup CLI commands."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.commands.backup_commands import backup_commands
from click.testing import CliRunner
from core.domain.value_objects.restore_result import (
    ComponentRestoreResult,
    RestoreResult,
)


class TestBackupRestoreCommand:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def _obj(self, restore_result):
        obj = MagicMock()
        obj.console = MagicMock()
        use_case = MagicMock()
        use_case.restore = AsyncMock(return_value=restore_result)
        obj.container.get_restore_device_config_interactor.return_value = use_case
        return obj

    def test_restore_exits_nonzero_on_failure(self, runner):
        result_vo = RestoreResult(
            success=False,
            device_ip="192.168.1.100",
            backup_id=1,
            total=1,
            succeeded=0,
            failed=1,
            skipped=0,
            components=[
                ComponentRestoreResult(
                    key="switch:0", action="SetConfig", success=False, error="boom"
                )
            ],
        )
        result = runner.invoke(
            backup_commands,
            ["restore", "1", "-t", "192.168.1.100", "--force"],
            obj=self._obj(result_vo),
        )
        assert result.exit_code == 1

    def test_restore_exits_zero_on_success(self, runner):
        result_vo = RestoreResult(
            success=True,
            device_ip="192.168.1.100",
            backup_id=1,
            total=1,
            succeeded=1,
            failed=0,
            skipped=0,
            components=[
                ComponentRestoreResult(key="switch:0", action="SetConfig", success=True)
            ],
        )
        result = runner.invoke(
            backup_commands,
            ["restore", "1", "-t", "192.168.1.100", "--force"],
            obj=self._obj(result_vo),
        )
        assert result.exit_code == 0
