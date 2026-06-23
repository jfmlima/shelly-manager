"""Tests for the backup schedule CLI subgroup."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.commands.backup_commands import backup_commands
from click.testing import CliRunner
from core.domain.entities.backup_schedule import BackupSchedule
from core.use_cases.run_due_backups import ScheduleRunResult


def _schedule(**kwargs):
    base = {"id": 1, "name": "nightly", "interval_seconds": 86400, "enabled": True}
    base.update(kwargs)
    return BackupSchedule(**base)


class TestScheduleCommands:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def _obj(self, *, manage=None, runner_uc=None):
        obj = MagicMock()
        obj.console = MagicMock()
        obj.container.get_manage_backup_schedules_interactor.return_value = (
            manage or MagicMock()
        )
        obj.container.get_run_due_backups_interactor.return_value = (
            runner_uc or MagicMock()
        )
        return obj

    def test_it_create_resolves_preset_interval(self, runner):
        captured = {}
        manage = MagicMock()

        async def create(schedule):
            captured["interval"] = schedule.interval_seconds
            captured["targets"] = schedule.target_ips
            schedule.id = 7
            return schedule

        manage.create_schedule = AsyncMock(side_effect=create)

        result = runner.invoke(
            backup_commands,
            [
                "schedule",
                "create",
                "--name",
                "daily-job",
                "--every",
                "daily",
                "-t",
                "192.168.1.10",
            ],
            obj=self._obj(manage=manage),
        )

        assert result.exit_code == 0
        assert captured["interval"] == 86400
        assert captured["targets"] == ["192.168.1.10"]

    def test_it_create_rejects_both_cadence_sources(self, runner):
        result = runner.invoke(
            backup_commands,
            [
                "schedule",
                "create",
                "--name",
                "x",
                "--every",
                "daily",
                "--interval-seconds",
                "3600",
                "-t",
                "192.168.1.10",
            ],
            obj=self._obj(),
        )
        assert result.exit_code != 0

    def test_it_create_rejects_no_targets(self, runner):
        result = runner.invoke(
            backup_commands,
            ["schedule", "create", "--name", "x", "--every", "daily"],
            obj=self._obj(),
        )
        assert result.exit_code != 0

    def test_it_list_renders_without_error(self, runner):
        manage = MagicMock()
        manage.list_schedules = AsyncMock(
            return_value=[_schedule(target_ips=["192.168.1.10"], next_run_at=1000)]
        )

        result = runner.invoke(
            backup_commands,
            ["schedule", "list"],
            obj=self._obj(manage=manage),
        )
        assert result.exit_code == 0

    def test_it_run_exits_nonzero_on_failure(self, runner):
        runner_uc = MagicMock()
        runner_uc.run_schedule = AsyncMock(
            return_value=ScheduleRunResult(
                schedule_id=1,
                schedule_name="nightly",
                status="failed",
                targets=1,
                failed=1,
            )
        )

        result = runner.invoke(
            backup_commands,
            ["schedule", "run", "1"],
            obj=self._obj(runner_uc=runner_uc),
        )
        assert result.exit_code == 1

    def test_it_run_exits_zero_on_ok(self, runner):
        runner_uc = MagicMock()
        runner_uc.run_schedule = AsyncMock(
            return_value=ScheduleRunResult(
                schedule_id=1,
                schedule_name="nightly",
                status="ok",
                targets=1,
                ok=1,
            )
        )

        result = runner.invoke(
            backup_commands,
            ["schedule", "run", "1"],
            obj=self._obj(runner_uc=runner_uc),
        )
        assert result.exit_code == 0
