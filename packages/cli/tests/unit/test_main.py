"""
Tests for the main CLI module.
"""

import pytest
from cli.main import cli
from click.testing import CliRunner


class TestCLIMain:

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_it_shows_help_when_no_command_provided(self, runner):
        result = runner.invoke(cli, [])

        assert result.exit_code == 0
        assert "Shelly Manager" in result.output
        assert "Smart home device management tool" in result.output

    def test_it_shows_version_information(self, runner):
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "Shelly Manager CLI" in result.output
        assert "Version:" in result.output

    def test_it_accepts_verbose_flag(self, runner):
        result = runner.invoke(cli, ["--verbose"])

        assert result.exit_code == 0

    # test_it_accepts_config_file_option removed as --config was removed

    def test_it_shows_help_for_available_commands(self, runner):
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "device" in result.output
        assert "export" in result.output
        assert "export" in result.output
        assert "scan" in result.output
