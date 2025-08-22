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

    def test_devices_command_shows_help(self, mock_container):
        runner = CliRunner()
        result = runner.invoke(
            export_commands, ["devices", "--help"], obj=mock_container
        )

        assert result.exit_code == 0

    def test_devices_command_requires_target_specification(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(
            export_commands,
            ["devices", "--output", "test_output.json"],
            obj=cli_context,
        )

        assert result.exit_code != 0
        assert "Aborted" in result.output
