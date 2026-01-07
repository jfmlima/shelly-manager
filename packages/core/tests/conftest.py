"""Test fixtures for core package tests."""

import os

# Generate a valid Fernet key for tests before any other imports.
# This must happen before settings.py is imported.
# NOTE: isort:skip and fmt:off are used to prevent linters from reordering.
if "SHELLY_SECRET_KEY" not in os.environ:  # noqa: E402
    from cryptography.fernet import Fernet

    os.environ["SHELLY_SECRET_KEY"] = Fernet.generate_key().decode()

from datetime import datetime  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

import pytest  # noqa: E402
from core.domain.entities.discovered_device import DiscoveredDevice  # noqa: E402
from core.domain.enums.enums import Status  # noqa: E402
from core.domain.value_objects.action_result import ActionResult  # noqa: E402
from core.domain.value_objects.scan_request import ScanRequest  # noqa: E402
from core.gateways.device import DeviceGateway  # noqa: E402


@pytest.fixture
def mock_device_gateway():
    gateway = MagicMock(spec=DeviceGateway)
    return gateway


@pytest.fixture
def sample_discovered_device():
    return DiscoveredDevice(
        ip="192.168.1.100",
        status=Status.DETECTED,
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
    return DiscoveredDevice(
        ip="192.168.1.101",
        status=Status.UNREACHABLE,
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
