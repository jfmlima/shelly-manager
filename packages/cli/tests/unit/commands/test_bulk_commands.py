"""
Tests for bulk commands.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.commands.bulk_commands import bulk
from cli.exceptions import EXIT_VALIDATION
from click.testing import CliRunner
from core.domain.value_objects.action_result import ActionResult


class TestBulkCommands:
    """Test suite for bulk commands."""

    @pytest.fixture
    def runner(self):
        """Create a Click CLI runner."""
        return CliRunner()

    @pytest.fixture
    def mock_context(self):
        """Create a mock CLI context."""
        mock_ctx = MagicMock()
        mock_ctx.obj = MagicMock()
        mock_ctx.obj.console = MagicMock()
        mock_ctx.obj.container = MagicMock()
        return mock_ctx

    def test_bulk_group_help(self, runner):
        """Test bulk command group shows help."""
        result = runner.invoke(bulk, ["--help"])
        assert result.exit_code == 0
        assert "Bulk operations on multiple devices" in result.output
        assert "reboot" in result.output
        assert "update" in result.output

    def test_bulk_reboot_help(self, runner):
        result = runner.invoke(bulk, ["reboot", "--help"])
        assert result.exit_code == 0
        assert "Reboot devices" in result.output
        assert "--target" in result.output
        assert "--force" in result.output
        assert "--workers" in result.output

    def test_bulk_update_help(self, runner):
        result = runner.invoke(bulk, ["update", "--help"])
        assert result.exit_code == 0
        assert "Update device firmware" in result.output
        assert "--target" in result.output
        assert "--channel" in result.output
        assert "--source" in result.output
        assert "--force" in result.output
        assert "--workers" in result.output

    def test_bulk_reboot_reboots_every_targeted_device(
        self, runner, cli_context, sample_devices
    ):
        execute = _answering_devices(cli_context, sample_devices)

        result = runner.invoke(
            bulk,
            ["reboot", "-t", "192.168.1.100", "-t", "192.168.1.101", "--force"],
            obj=cli_context,
        )

        assert result.exit_code == 0, result.output
        assert [
            (call.args[0].device_ip, call.args[0].component_key, call.args[0].action)
            for call in execute.await_args_list
        ] == [
            ("192.168.1.100", "shelly", "Reboot"),
            ("192.168.1.101", "shelly", "Reboot"),
        ]

    def test_bulk_update_updates_every_targeted_device_on_the_channel(
        self, runner, cli_context, sample_devices
    ):
        execute = _answering_devices(cli_context, sample_devices)

        result = runner.invoke(
            bulk,
            ["update", "192.168.1.100", "--channel", "beta", "--force"],
            obj=cli_context,
        )

        assert result.exit_code == 0, result.output
        request = execute.await_args_list[0].args[0]
        assert (request.component_key, request.action) == ("shelly", "Update")
        assert request.parameters == {"stage": "beta"}

    def test_bulk_update_serves_firmware_from_the_local_store(
        self, runner, cli_context, sample_device
    ):
        _answering_devices(cli_context, [sample_device])
        local = cli_context.container.get_update_device_from_local_interactor()
        local.execute = AsyncMock(
            return_value=ActionResult(
                success=True,
                action_type="shelly.Update",
                device_ip=sample_device.ip,
                message="Update initiated",
            )
        )

        result = runner.invoke(
            bulk,
            ["update", "-t", sample_device.ip, "--source", "local", "--force"],
            obj=cli_context,
        )

        assert result.exit_code == 0, result.output
        local.execute.assert_awaited_once()

    def test_bulk_config_apply_rejects_non_configurable_component_types(
        self, runner, mock_context
    ):
        result = runner.invoke(
            bulk,
            [
                "config",
                "apply",
                "-t",
                "192.168.1.10",
                "--component",
                "schedules",
                "--config",
                '{"jobs": []}',
                "--force",
            ],
            obj=mock_context.obj,
        )

        assert result.exit_code == EXIT_VALIDATION

    def test_bulk_config_export_rejects_unknown_component_types(
        self, runner, mock_context
    ):
        result = runner.invoke(
            bulk,
            [
                "config",
                "export",
                "-t",
                "192.168.1.10",
                "--components",
                "swich",
                "--output",
                "out.json",
            ],
            obj=mock_context.obj,
        )

        assert result.exit_code == EXIT_VALIDATION

    def test_bulk_update_invalid_channel(self, runner, mock_context):
        """Test bulk update with invalid channel fails."""
        with runner.isolated_filesystem():
            result = runner.invoke(
                bulk,
                [
                    "update",
                    "--target",
                    "192.168.1.100",
                    "--channel",
                    "invalid",
                    "--force",
                ],
                obj=mock_context.obj,
            )

        assert result.exit_code != 0
        assert "Invalid value for '--channel'" in result.output


def _answering_devices(cli_context, devices):
    """Discovery finds ``devices``; every action on them succeeds."""
    cli_context.container.get_scan_interactor().execute = AsyncMock(
        return_value=devices
    )
    execute = AsyncMock(
        side_effect=lambda request: ActionResult(
            success=True,
            action_type=f"{request.component_key}.{request.action}",
            device_ip=request.device_ip,
            message="done",
        )
    )
    cli_context.container.get_execute_component_action_interactor().execute = execute
    return execute
