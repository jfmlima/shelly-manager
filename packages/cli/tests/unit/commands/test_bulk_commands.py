"""
Tests for bulk commands.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.commands.bulk_commands import bulk
from click.testing import CliRunner


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

    @pytest.fixture
    def mock_bulk_use_case(self):
        """Create a mock bulk operations use case."""
        mock_use_case = MagicMock()
        mock_use_case.execute_bulk_reboot = AsyncMock()
        mock_use_case.execute_bulk_update = AsyncMock()
        mock_use_case.display_bulk_results = MagicMock()
        return mock_use_case

    def test_bulk_group_help(self, runner):
        """Test bulk command group shows help."""
        result = runner.invoke(bulk, ["--help"])
        assert result.exit_code == 0
        assert "Bulk operations on multiple devices" in result.output
        assert "reboot" in result.output
        assert "update" in result.output

    def test_bulk_reboot_help(self, runner):
        """Test bulk reboot command shows help."""
        result = runner.invoke(bulk, ["reboot", "--help"])
        assert result.exit_code == 0
        assert "Reboot multiple devices" in result.output
        assert "--target" in result.output
        assert "--force" in result.output
        assert "--workers" in result.output

    def test_bulk_update_help(self, runner):
        """Test bulk update command shows help."""
        result = runner.invoke(bulk, ["update", "--help"])
        assert result.exit_code == 0
        assert "Update firmware on multiple devices" in result.output
        assert "--target" in result.output
        assert "--channel" in result.output
        assert "--force" in result.output
        assert "--workers" in result.output

    def test_bulk_reboot_command_structure(self, runner):
        """Test bulk reboot command structure and options."""
        result = runner.invoke(bulk, ["reboot", "--help"])
        assert result.exit_code == 0
        assert result.exit_code == 0
        assert "--target" in result.output
        assert "--force" in result.output
        assert "--workers" in result.output

    def test_bulk_update_command_structure(self, runner):
        """Test bulk update command structure and options."""
        result = runner.invoke(bulk, ["update", "--help"])
        assert result.exit_code == 0
        assert result.exit_code == 0
        assert "--target" in result.output
        assert "--channel" in result.output
        assert "--force" in result.output
        assert "--workers" in result.output

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
