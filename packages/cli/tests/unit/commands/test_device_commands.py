from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.commands.device_commands import device_commands, scan
from click.testing import CliRunner


class TestDeviceCommands:

    def test_device_commands_group_exists(self):
        assert device_commands.name == "device-commands"
        assert len(device_commands.commands) > 0

    def test_scan_command_in_group(self):
        assert "scan" in device_commands.commands

    def test_list_command_in_group(self):
        assert "list" in device_commands.commands

    def test_status_command_in_group(self):
        assert "status" in device_commands.commands

    def test_actions_command_in_group(self):
        assert "actions" in device_commands.commands
        actions_group = device_commands.commands["actions"]
        assert "list" in actions_group.commands
        assert "execute" in actions_group.commands
        assert "reboot" in device_commands.commands
        assert "update" in device_commands.commands
        assert "toggle" in device_commands.commands

    def test_device_commands_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(device_commands, ["--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "scan" in result.output
        assert "list" in result.output
        assert "status" in result.output
        assert "component" in result.output


class TestScanCommand:

    @pytest.fixture
    def mock_scan_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_scan(self, cli_context, mock_scan_interactor):
        cli_context.container.get_scan_interactor.return_value = mock_scan_interactor
        return cli_context

    def test_scan_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(device_commands, ["scan", "--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "Scan for Shelly devices" in result.output

    def test_scan_with_ip_range_success(
        self, cli_context_with_scan, sample_devices, mock_scan_interactor
    ):
        mock_scan_interactor.execute.return_value = sample_devices

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["scan", "192.168.1.1-192.168.1.50"],
            obj=cli_context_with_scan,
        )

        assert result.exit_code == 0
        mock_scan_interactor.execute.assert_called_once()

    def test_scan_with_from_config(
        self, cli_context_with_scan, sample_devices, mock_scan_interactor
    ):
        mock_scan_interactor.execute.return_value = sample_devices

        runner = CliRunner()
        result = runner.invoke(
            device_commands, ["scan", "--from-config"], obj=cli_context_with_scan
        )

        assert result.exit_code == 0
        mock_scan_interactor.execute.assert_called_once()

    def test_scan_no_devices_found(self, cli_context_with_scan, mock_scan_interactor):
        mock_scan_interactor.execute.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["scan", "192.168.1.1-192.168.1.50"],
            obj=cli_context_with_scan,
        )

        assert result.exit_code == 0
        mock_scan_interactor.execute.assert_called_once()

    def test_scan_with_specific_devices(
        self, cli_context_with_scan, sample_devices, mock_scan_interactor
    ):
        mock_scan_interactor.execute.return_value = sample_devices

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["scan", "--devices", "192.168.1.100", "--devices", "192.168.1.101"],
            obj=cli_context_with_scan,
        )

        assert result.exit_code == 0
        mock_scan_interactor.execute.assert_called_once()

    def test_scan_with_custom_timeout_and_workers(
        self, cli_context_with_scan, sample_devices, mock_scan_interactor
    ):
        mock_scan_interactor.execute.return_value = sample_devices

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["scan", "192.168.1.1-192.168.1.50", "--timeout", "5", "--workers", "20"],
            obj=cli_context_with_scan,
        )

        assert result.exit_code == 0
        mock_scan_interactor.execute.assert_called_once()

        call_args = mock_scan_interactor.execute.call_args[0][0]
        assert call_args.timeout == 5.0
        assert call_args.max_workers == 20


class TestListCommand:

    @pytest.fixture
    def mock_scan_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_list(self, cli_context, mock_scan_interactor):
        cli_context.container.get_scan_interactor.return_value = mock_scan_interactor
        return cli_context

    def test_list_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(device_commands, ["list", "--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "List Shelly devices" in result.output

    def test_list_devices_success(
        self, cli_context_with_list, sample_devices, mock_scan_interactor
    ):
        mock_scan_interactor.execute.return_value = sample_devices

        runner = CliRunner()
        result = runner.invoke(
            device_commands, ["list", "--from-config"], obj=cli_context_with_list
        )

        assert result.exit_code == 0
        mock_scan_interactor.execute.assert_called_once()

    def test_list_no_devices(self, cli_context_with_list, mock_scan_interactor):
        mock_scan_interactor.execute.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            device_commands, ["list", "--from-config"], obj=cli_context_with_list
        )

        assert result.exit_code == 0
        mock_scan_interactor.execute.assert_called_once()


class TestStatusCommand:

    @pytest.fixture
    def mock_status_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def mock_scan_interactor_for_status(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_status(
        self, cli_context, mock_status_interactor, mock_scan_interactor_for_status
    ):
        cli_context.container.get_status_interactor.return_value = (
            mock_status_interactor
        )
        cli_context.container.get_scan_interactor.return_value = (
            mock_scan_interactor_for_status
        )
        return cli_context

    def test_status_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(device_commands, ["status", "--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "Check status of specific Shelly devices" in result.output

    def test_status_no_devices_specified(self, cli_context_with_status):
        runner = CliRunner()
        result = runner.invoke(device_commands, ["status"], obj=cli_context_with_status)

        assert result.exit_code != 0

    def test_status_specific_devices_success(
        self, cli_context_with_status, mock_status_interactor, sample_device
    ):
        mock_status_interactor.execute.return_value = sample_device

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["status", "192.168.1.100", "192.168.1.101"],
            obj=cli_context_with_status,
        )

        assert result.exit_code == 0
        assert mock_status_interactor.execute.call_count == 2

    def test_status_from_config(
        self,
        cli_context_with_status,
        mock_status_interactor,
        mock_scan_interactor_for_status,
        sample_devices,
        sample_device,
    ):
        mock_scan_interactor_for_status.execute.return_value = sample_devices
        mock_status_interactor.execute.return_value = sample_device

        runner = CliRunner()
        result = runner.invoke(
            device_commands, ["status", "--from-config"], obj=cli_context_with_status
        )

        assert result.exit_code == 0
        mock_scan_interactor_for_status.execute.assert_called_once()
        assert mock_status_interactor.execute.call_count == 2

    def test_status_device_error(self, cli_context_with_status, mock_status_interactor):
        mock_status_interactor.execute.side_effect = Exception("Connection timeout")

        runner = CliRunner()
        result = runner.invoke(
            device_commands, ["status", "192.168.1.100"], obj=cli_context_with_status
        )

        assert result.exit_code == 0
        mock_status_interactor.execute.assert_called_once()

    def test_status_verbose_error_output(
        self, cli_context_with_status, mock_status_interactor
    ):
        cli_context_with_status.verbose = True
        mock_status_interactor.execute.side_effect = Exception("Connection timeout")

        runner = CliRunner()
        result = runner.invoke(
            device_commands, ["status", "192.168.1.100"], obj=cli_context_with_status
        )

        assert result.exit_code == 0


class TestDeviceRebootCommand:

    @pytest.fixture
    def mock_execute_component_action_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_component_reboot(
        self, cli_context, mock_execute_component_action_interactor
    ):
        cli_context.container.get_execute_component_action_interactor.return_value = (
            mock_execute_component_action_interactor
        )
        mock_scan_interactor = cli_context.container.get_scan_interactor.return_value
        mock_scan_interactor.execute.return_value = []
        return cli_context

    def test_device_reboot_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(device_commands, ["reboot", "--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "Reboot devices" in result.output

    def test_device_reboot_no_devices_specified(
        self, cli_context_with_component_reboot
    ):
        runner = CliRunner()
        result = runner.invoke(
            device_commands, ["reboot"], obj=cli_context_with_component_reboot
        )

        assert result.exit_code != 0

    def test_device_reboot_with_force_flag(
        self,
        cli_context_with_component_reboot,
        mock_execute_component_action_interactor,
        sample_action_result,
    ):
        mock_execute_component_action_interactor.execute.return_value = (
            sample_action_result
        )

        mock_scan_interactor = (
            cli_context_with_component_reboot.container.get_scan_interactor.return_value
        )
        mock_scan_interactor.execute.return_value = ["192.168.1.100"]

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["reboot", "--devices", "192.168.1.100", "--force"],
            obj=cli_context_with_component_reboot,
        )

        assert result.exit_code == 0
        mock_execute_component_action_interactor.execute.assert_called_once()

    def test_device_reboot_user_cancellation(
        self,
        cli_context_with_component_reboot,
        mock_execute_component_action_interactor,
    ):
        mock_scan_interactor = (
            cli_context_with_component_reboot.container.get_scan_interactor.return_value
        )
        mock_scan_interactor.execute.return_value = ["192.168.1.100"]

        cli_context_with_component_reboot.console.input.return_value = "n"

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["reboot", "--devices", "192.168.1.100"],
            obj=cli_context_with_component_reboot,
            input="n\n",
        )

        assert result.exit_code == 0
        cli_context_with_component_reboot.console.input.assert_called_once_with(
            "\nContinue? [y/N]: "
        )
        mock_execute_component_action_interactor.execute.assert_not_called()

    def test_device_reboot_from_config_with_confirmation(
        self,
        cli_context_with_component_reboot,
        mock_execute_component_action_interactor,
        sample_action_result,
    ):
        mock_execute_component_action_interactor.execute.return_value = (
            sample_action_result
        )

        mock_scan_interactor = (
            cli_context_with_component_reboot.container.get_scan_interactor.return_value
        )
        mock_scan_interactor.execute.return_value = ["192.168.1.100"]

        cli_context_with_component_reboot.console.input.return_value = "y"

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["reboot", "--from-config"],
            obj=cli_context_with_component_reboot,
            input="y\n",
        )

        assert result.exit_code == 0
        assert mock_execute_component_action_interactor.execute.call_count >= 1

    def test_device_reboot_device_error(
        self,
        cli_context_with_component_reboot,
        mock_execute_component_action_interactor,
    ):
        mock_execute_component_action_interactor.execute.side_effect = Exception(
            "Connection failed"
        )

        mock_scan_interactor = (
            cli_context_with_component_reboot.container.get_scan_interactor.return_value
        )
        mock_scan_interactor.execute.return_value = ["192.168.1.100"]

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            ["reboot", "--devices", "192.168.1.100", "--force"],
            obj=cli_context_with_component_reboot,
        )

        assert result.exit_code == 0
        mock_execute_component_action_interactor.execute.assert_called_once()

    def test_device_reboot_mixed_results(
        self,
        cli_context_with_component_reboot,
        mock_execute_component_action_interactor,
        sample_action_result,
    ):
        failed_result = AsyncMock()
        failed_result.success = False
        failed_result.message = "Connection failed"

        mock_execute_component_action_interactor.execute.side_effect = [
            sample_action_result,
            failed_result,
        ]

        mock_scan_interactor = (
            cli_context_with_component_reboot.container.get_scan_interactor.return_value
        )
        mock_scan_interactor.execute.return_value = ["192.168.1.100", "192.168.1.101"]

        runner = CliRunner()
        result = runner.invoke(
            device_commands,
            [
                "reboot",
                "--devices",
                "192.168.1.100",
                "--devices",
                "192.168.1.101",
                "--force",
            ],
            obj=cli_context_with_component_reboot,
        )

        assert result.exit_code == 0
        assert mock_execute_component_action_interactor.execute.call_count == 2


class TestStandaloneScandCommand:

    @pytest.fixture
    def mock_scan_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_standalone_scan(self, cli_context, mock_scan_interactor):
        cli_context.container.get_scan_interactor.return_value = mock_scan_interactor
        return cli_context

    def test_standalone_scan_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(scan, ["--help"], obj=cli_context)

        assert result.exit_code == 0

    def test_standalone_scan_success(
        self, cli_context_with_standalone_scan, sample_devices, mock_scan_interactor
    ):
        mock_scan_interactor.execute.return_value = sample_devices

        runner = CliRunner()
        result = runner.invoke(
            scan, ["192.168.1.1-192.168.1.50"], obj=cli_context_with_standalone_scan
        )

        assert result.exit_code == 0
        mock_scan_interactor.execute.assert_called_once()


class TestActionsCommands:
    """Tests for actions subcommand group and convenience commands."""

    def test_actions_subcommand_group_exists(self):
        """Test that actions subcommand group exists under device commands."""
        assert "actions" in device_commands.commands
        actions_group = device_commands.commands["actions"]
        assert len(actions_group.commands) > 0

    def test_actions_list_command_exists(self):
        """Test that list command exists in actions group."""
        actions_group = device_commands.commands["actions"]
        assert "list" in actions_group.commands

    def test_actions_execute_command_exists(self):
        """Test that execute command exists in actions group."""
        actions_group = device_commands.commands["actions"]
        assert "execute" in actions_group.commands

    def test_device_convenience_commands_exist(self):
        """Test that convenience commands exist directly under device."""
        assert "reboot" in device_commands.commands
        assert "update" in device_commands.commands
        assert "toggle" in device_commands.commands

    def test_actions_help(self, cli_context):
        """Test actions subcommand help displays correctly."""
        runner = CliRunner()
        result = runner.invoke(device_commands, ["actions", "--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "list" in result.output
        assert "execute" in result.output

    def test_device_update_help(self, cli_context):
        """Test device update command help."""
        runner = CliRunner()
        result = runner.invoke(device_commands, ["update", "--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "Update device firmware" in result.output

    def test_actions_execute_help(self, cli_context):
        """Test actions execute command help."""
        runner = CliRunner()
        result = runner.invoke(
            device_commands, ["actions", "execute", "--help"], obj=cli_context
        )

        assert result.exit_code == 0
        assert "Execute action on device components" in result.output

    def test_device_update_requires_device_specification(self, cli_context):
        """Test that device update requires device specification."""
        mock_scan_interactor = cli_context.container.get_scan_interactor.return_value
        mock_scan_interactor.execute.return_value = []

        cli_context.container.get_execute_component_action_interactor.return_value = (
            MagicMock()
        )

        runner = CliRunner()
        result = runner.invoke(device_commands, ["update"], obj=cli_context)

        assert result.exit_code != 0

    def test_actions_execute_requires_parameters(self, cli_context):
        """Test that actions execute requires component and action parameters."""
        runner = CliRunner()
        result = runner.invoke(device_commands, ["actions", "execute"], obj=cli_context)

        assert result.exit_code != 0
