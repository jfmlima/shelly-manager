"""Tests for the provisioning CLI commands."""

from unittest.mock import AsyncMock

import pytest
from cli.commands.provision_commands import provision_commands
from click.testing import CliRunner
from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.domain.value_objects.provision_request import (
    APDeviceInfo,
    ProvisionResult,
    ProvisionStep,
)


class TestProvisionCommands:
    def test_provision_commands_group_exists(self):
        assert provision_commands.name == "provision"
        assert len(provision_commands.commands) > 0

    def test_detect_command_in_group(self):
        assert "detect" in provision_commands.commands

    def test_run_command_in_group(self):
        assert "run" in provision_commands.commands

    def test_profiles_subgroup_in_group(self):
        assert "profiles" in provision_commands.commands
        profiles_group = provision_commands.commands["profiles"]
        assert "list" in profiles_group.commands
        assert "create" in profiles_group.commands
        assert "delete" in profiles_group.commands
        assert "set-default" in profiles_group.commands

    def test_provision_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(provision_commands, ["--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "detect" in result.output
        assert "run" in result.output
        assert "profiles" in result.output


class TestDetectCommand:
    @pytest.fixture
    def mock_provision_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_provision(self, cli_context, mock_provision_interactor):
        cli_context.container.get_provision_device_interactor.return_value = (
            mock_provision_interactor
        )
        return cli_context

    def test_detect_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(
            provision_commands, ["detect", "--help"], obj=cli_context
        )

        assert result.exit_code == 0
        assert "Detect a Shelly device" in result.output

    def test_detect_device_success(
        self, cli_context_with_provision, mock_provision_interactor
    ):
        mock_provision_interactor.detect.return_value = APDeviceInfo(
            device_id="shellyplus1pm-a4cf12f45678",
            mac="A4CF12F45678",
            model="SNSW-001P16EU",
            generation=2,
            firmware_version="1.4.4",
            auth_enabled=False,
            auth_domain="shellyplus1pm-a4cf12f45678",
            app="Plus1PM",
        )

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["detect", "--ip", "192.168.33.1"],
            obj=cli_context_with_provision,
        )

        assert result.exit_code == 0
        mock_provision_interactor.detect.assert_called_once()

    def test_detect_device_default_ip(
        self, cli_context_with_provision, mock_provision_interactor
    ):
        mock_provision_interactor.detect.return_value = APDeviceInfo(
            device_id="shellyplus1pm-a4cf12f45678",
            mac="A4CF12F45678",
            model="SNSW-001P16EU",
            generation=2,
            firmware_version="1.4.4",
            auth_enabled=False,
        )

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["detect"],
            obj=cli_context_with_provision,
        )

        assert result.exit_code == 0
        call_args = mock_provision_interactor.detect.call_args[0][0]
        assert call_args.device_ip == "192.168.33.1"

    def test_detect_device_failure_aborts(
        self, cli_context_with_provision, mock_provision_interactor
    ):
        mock_provision_interactor.detect.side_effect = Exception("Connection refused")

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["detect"],
            obj=cli_context_with_provision,
        )

        assert result.exit_code != 0


class TestRunProvisionCommand:
    @pytest.fixture
    def mock_provision_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def mock_profiles_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_provision(
        self, cli_context, mock_provision_interactor, mock_profiles_interactor
    ):
        cli_context.container.get_provision_device_interactor.return_value = (
            mock_provision_interactor
        )
        cli_context.container.get_manage_profiles_interactor.return_value = (
            mock_profiles_interactor
        )
        return cli_context

    def test_run_help(self, cli_context):
        runner = CliRunner()
        result = runner.invoke(provision_commands, ["run", "--help"], obj=cli_context)

        assert result.exit_code == 0
        assert "Provision a new Shelly device" in result.output

    def test_run_provision_success(
        self, cli_context_with_provision, mock_provision_interactor
    ):
        mock_provision_interactor.execute.return_value = ProvisionResult(
            success=True,
            device_id="shellyplus1pm-a4cf12f45678",
            device_model="SNSW-001P16EU",
            device_mac="A4CF12F45678",
            generation=2,
            steps_completed=[
                ProvisionStep(name="Sys.SetConfig", success=True, message="OK"),
                ProvisionStep(name="WiFi.STA.SetConfig", success=True, message="OK"),
            ],
            steps_failed=[],
            needs_verification=False,
        )

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["run"],
            obj=cli_context_with_provision,
        )

        assert result.exit_code == 0
        mock_provision_interactor.execute.assert_called_once()

    def test_run_provision_with_profile_name(
        self,
        cli_context_with_provision,
        mock_provision_interactor,
        mock_profiles_interactor,
    ):
        mock_profiles_interactor.list_profiles.return_value = [
            ProvisioningProfile(id=5, name="my-profile", is_default=False),
        ]
        mock_provision_interactor.execute.return_value = ProvisionResult(
            success=True,
            device_id="test-device",
            device_model="TestModel",
            device_mac="AABBCCDDEEFF",
            generation=2,
            steps_completed=[],
            steps_failed=[],
            needs_verification=False,
        )

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["run", "--profile", "my-profile"],
            obj=cli_context_with_provision,
        )

        assert result.exit_code == 0
        mock_profiles_interactor.list_profiles.assert_called_once()
        call_args = mock_provision_interactor.execute.call_args[0][0]
        assert call_args.profile_id == 5

    def test_run_provision_with_unknown_profile_aborts(
        self, cli_context_with_provision, mock_profiles_interactor
    ):
        mock_profiles_interactor.list_profiles.return_value = [
            ProvisioningProfile(id=1, name="other", is_default=False),
        ]

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["run", "--profile", "nonexistent"],
            obj=cli_context_with_provision,
        )

        assert result.exit_code != 0

    def test_run_provision_failure_aborts(
        self, cli_context_with_provision, mock_provision_interactor
    ):
        mock_provision_interactor.execute.return_value = ProvisionResult(
            success=False,
            error="WiFi configuration failed",
            steps_completed=[],
            steps_failed=[
                ProvisionStep(
                    name="WiFi.STA.SetConfig", success=False, message="timeout"
                )
            ],
            needs_verification=False,
        )

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["run"],
            obj=cli_context_with_provision,
        )

        assert result.exit_code != 0


class TestProfileListCommand:
    @pytest.fixture
    def mock_profiles_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_profiles(self, cli_context, mock_profiles_interactor):
        cli_context.container.get_manage_profiles_interactor.return_value = (
            mock_profiles_interactor
        )
        return cli_context

    def test_list_profiles_empty(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.list_profiles.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["profiles", "list"],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code == 0
        mock_profiles_interactor.list_profiles.assert_called_once()

    def test_list_profiles_with_data(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.list_profiles.return_value = [
            ProvisioningProfile(
                id=1,
                name="home",
                wifi_ssid="HomeNet",
                mqtt_enabled=True,
                mqtt_server="mqtt.local:1883",
                auth_password="secret",
                is_default=True,
            ),
            ProvisioningProfile(
                id=2,
                name="office",
                wifi_ssid="OfficeNet",
                is_default=False,
            ),
        ]

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["profiles", "list"],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code == 0
        mock_profiles_interactor.list_profiles.assert_called_once()


class TestProfileCreateCommand:
    @pytest.fixture
    def mock_profiles_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_profiles(self, cli_context, mock_profiles_interactor):
        cli_context.container.get_manage_profiles_interactor.return_value = (
            mock_profiles_interactor
        )
        return cli_context

    def test_create_profile_success(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.create_profile.return_value = ProvisioningProfile(
            id=1,
            name="test-profile",
            wifi_ssid="TestNet",
            is_default=True,
        )

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            [
                "profiles",
                "create",
                "--name",
                "test-profile",
                "--wifi-ssid",
                "TestNet",
                "--wifi-password",
                "secret",
            ],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code == 0
        mock_profiles_interactor.create_profile.assert_called_once()

    def test_create_profile_with_mqtt(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.create_profile.return_value = ProvisioningProfile(
            id=1,
            name="mqtt-profile",
            mqtt_enabled=True,
            mqtt_server="mqtt.local:1883",
            is_default=False,
        )

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            [
                "profiles",
                "create",
                "--name",
                "mqtt-profile",
                "--mqtt-server",
                "mqtt.local:1883",
                "--mqtt-user",
                "admin",
                "--mqtt-password",
                "pass",
            ],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code == 0
        mock_profiles_interactor.create_profile.assert_called_once()
        call_args = mock_profiles_interactor.create_profile.call_args[0][0]
        assert call_args.mqtt_enabled is True
        assert call_args.mqtt_server == "mqtt.local:1883"

    def test_create_profile_requires_name(self, cli_context_with_profiles):
        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["profiles", "create"],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code != 0

    def test_create_profile_failure(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.create_profile.side_effect = Exception(
            "Profile already exists"
        )

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["profiles", "create", "--name", "existing"],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code != 0


class TestProfileDeleteCommand:
    @pytest.fixture
    def mock_profiles_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_profiles(self, cli_context, mock_profiles_interactor):
        cli_context.container.get_manage_profiles_interactor.return_value = (
            mock_profiles_interactor
        )
        return cli_context

    def test_delete_profile_success(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.list_profiles.return_value = [
            ProvisioningProfile(id=1, name="to-delete", is_default=False),
        ]
        mock_profiles_interactor.delete_profile.return_value = None

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["profiles", "delete", "to-delete"],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code == 0
        mock_profiles_interactor.delete_profile.assert_called_once_with(1)

    def test_delete_profile_not_found_aborts(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.list_profiles.return_value = [
            ProvisioningProfile(id=1, name="other", is_default=False),
        ]

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["profiles", "delete", "nonexistent"],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code != 0


class TestProfileSetDefaultCommand:
    @pytest.fixture
    def mock_profiles_interactor(self):
        interactor = AsyncMock()
        return interactor

    @pytest.fixture
    def cli_context_with_profiles(self, cli_context, mock_profiles_interactor):
        cli_context.container.get_manage_profiles_interactor.return_value = (
            mock_profiles_interactor
        )
        return cli_context

    def test_set_default_success(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.list_profiles.return_value = [
            ProvisioningProfile(id=2, name="my-profile", is_default=False),
        ]
        mock_profiles_interactor.set_default_profile.return_value = None

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["profiles", "set-default", "my-profile"],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code == 0
        mock_profiles_interactor.set_default_profile.assert_called_once_with(2)

    def test_set_default_not_found_aborts(
        self, cli_context_with_profiles, mock_profiles_interactor
    ):
        mock_profiles_interactor.list_profiles.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            provision_commands,
            ["profiles", "set-default", "nonexistent"],
            obj=cli_context_with_profiles,
        )

        assert result.exit_code != 0
