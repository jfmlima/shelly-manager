"""
Test configuration and shared fixtures for CLI tests.
"""

from unittest.mock import MagicMock

import pytest
from cli.main import CliContext
from click.testing import CliRunner
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status
from core.domain.value_objects.action_result import ActionResult
from core.domain.value_objects.scan_request import ScanRequest
from core.gateways.configuration import ConfigurationGateway
from core.gateways.device import DeviceGateway
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.reboot_device import RebootDeviceUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_device_gateway():
    gateway = MagicMock(spec=DeviceGateway)
    return gateway


@pytest.fixture
def mock_config_gateway():
    gateway = MagicMock(spec=ConfigurationGateway)
    return gateway


@pytest.fixture
def mock_scan_interactor():
    return MagicMock(spec=ScanDevicesUseCase)


@pytest.fixture
def mock_status_interactor():
    return MagicMock(spec=CheckDeviceStatusUseCase)


@pytest.fixture
def mock_reboot_interactor():
    return MagicMock(spec=RebootDeviceUseCase)


@pytest.fixture
def mock_update_interactor():
    return MagicMock(spec=UpdateDeviceFirmwareUseCase)


@pytest.fixture
def mock_config_get_interactor():
    return MagicMock(spec=GetConfigurationUseCase)


@pytest.fixture
def mock_config_set_interactor():
    return MagicMock(spec=SetConfigurationUseCase)


@pytest.fixture
def mock_container(
    mock_scan_interactor,
    mock_status_interactor,
    mock_reboot_interactor,
    mock_update_interactor,
    mock_config_get_interactor,
    mock_config_set_interactor,
):
    container = MagicMock()  # Remove spec restriction
    container.get_scan_interactor.return_value = mock_scan_interactor
    container.get_status_interactor.return_value = mock_status_interactor
    container.get_reboot_interactor.return_value = mock_reboot_interactor
    container.get_update_interactor.return_value = mock_update_interactor
    container.get_config_get_interactor.return_value = mock_config_get_interactor
    container.get_config_set_interactor.return_value = mock_config_set_interactor
    container.get_device_config_interactor.return_value = mock_config_get_interactor
    container.get_device_config_set_interactor.return_value = mock_config_set_interactor
    container.get_export_interactor.return_value = MagicMock()
    return container


@pytest.fixture
def mock_console():
    console = MagicMock()
    console.get_time.return_value = 0.0
    return console


@pytest.fixture
def cli_context(mock_container, mock_console):
    ctx = CliContext()
    ctx.container = mock_container
    ctx.console = mock_console
    ctx.verbose = False
    ctx.config_file = None
    return ctx


@pytest.fixture
def sample_device():
    return DiscoveredDevice(
        ip="192.168.1.100",
        status=Status.DETECTED,
        device_id="shelly1pm-test123",
        device_type="SHPM-1",
        firmware_version="20230913-114010/v1.14.0-gcb84623",
        device_name="Test Device",
        auth_required=False,
        response_time=0.1,
        has_update=False,
    )


@pytest.fixture
def sample_devices(sample_device):
    device2 = DiscoveredDevice(
        ip="192.168.1.101",
        status=Status.DETECTED,
        device_id="shelly1pm-test124",
        device_type="SHPM-1",
        firmware_version="20230913-114010/v1.14.0-gcb84623",
        device_name="Test Device 2",
        auth_required=False,
        response_time=0.15,
        has_update=True,
    )
    return [sample_device, device2]


@pytest.fixture
def sample_action_result():
    return ActionResult(
        success=True,
        action_type="reboot",
        device_ip="192.168.1.100",
        message="Device rebooted successfully",
    )


@pytest.fixture
def sample_scan_request():
    return ScanRequest(
        device_ips=["192.168.1.100", "192.168.1.101"], timeout=3.0, max_workers=10
    )


@pytest.fixture
def sample_device_config():
    return {
        "wifi": {"sta": {"ssid": "TestWiFi", "enable": True}},
        "mqtt": {"enable": False},
        "name": "Test Device",
    }
