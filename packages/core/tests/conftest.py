from datetime import datetime
from unittest.mock import MagicMock

import pytest
from core.domain.entities.shelly_device import ShellyDevice
from core.domain.enums.enums import DeviceStatus
from core.domain.value_objects.action_result import ActionResult
from core.domain.value_objects.scan_request import ScanRequest
from core.gateways.configuration import ConfigurationGateway
from core.gateways.device import DeviceGateway


@pytest.fixture
def mock_device_gateway():
    gateway = MagicMock(spec=DeviceGateway)
    return gateway


@pytest.fixture
def mock_config_gateway():
    gateway = MagicMock(spec=ConfigurationGateway)
    return gateway


@pytest.fixture
def sample_shelly_device():
    return ShellyDevice(
        ip="192.168.1.100",
        status=DeviceStatus.DETECTED,
        device_id="shelly1pm-test123",
        device_type="SHPM-1",
        firmware_version="20230913-114010/v1.14.0-gcb84623",
        device_name="Test Device",
        auth_required=False,
        last_seen=datetime.now(),
        response_time=0.1,
        has_update=False,
    )


@pytest.fixture
def sample_offline_device():
    return ShellyDevice(
        ip="192.168.1.101",
        status=DeviceStatus.UNREACHABLE,
        device_id=None,
        device_type=None,
        firmware_version=None,
        device_name=None,
        auth_required=False,
        last_seen=None,
        response_time=None,
        error_message="Connection timeout",
    )


@pytest.fixture
def sample_action_result():
    return ActionResult(
        success=True,
        action_type="reboot",
        device_ip="192.168.1.100",
        message="Device rebooted successfully",
        timestamp=datetime.now(),
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
