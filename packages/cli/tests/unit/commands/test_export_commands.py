from unittest.mock import AsyncMock

from cli.commands.export_commands import export_commands
from click.testing import CliRunner


class TestExportCommands:

    def test_export_commands_group_exists(self):
        assert export_commands.name == "export-commands"
        assert len(export_commands.commands) > 0

    def test_devices_command_in_group(self):
        assert "devices" in export_commands.commands

    def test_export_commands_help(self, mock_container):
        runner = CliRunner()
        result = runner.invoke(export_commands, ["--help"], obj=mock_container)

        assert result.exit_code == 0
        assert "devices" in result.output

    def test_export_devices_with_targets(
        self,
        runner,
        cli_context,
        mock_scan_interactor,
        mock_status_interactor,
        sample_device_status,
    ):
        """Test export devices with specific targets."""
        mock_scan_interactor.execute = AsyncMock(return_value=[])
        mock_status_interactor.execute.return_value = sample_device_status

        with runner.isolated_filesystem():
            result = runner.invoke(
                export_commands.commands["devices"],
                ["-t", "192.168.1.100", "-t", "192.168.1.101", "--format", "json"],
                obj=cli_context,
            )

            assert result.exit_code == 0

    def test_devices_command_shows_help(self, mock_container):
        runner = CliRunner()
        result = runner.invoke(
            export_commands, ["devices", "--help"], obj=mock_container
        )

        assert result.exit_code == 0

    def test_devices_command_requires_target_specification(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(
            export_commands.commands["devices"],
            ["--output", "test_output.json"],
            obj=cli_context,
        )

        assert result.exit_code != 0
        assert (
            "Aborted" in result.output
            or "Missing" in result.output
            or "Error" in result.output
        )
