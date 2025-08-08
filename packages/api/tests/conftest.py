from datetime import datetime

import pytest
from api.main import create_app
from core.domain.entities.shelly_device import ShellyDevice
from core.domain.enums.enums import DeviceStatus
from core.domain.value_objects.action_result import ActionResult


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
        has_update=False,
        error_message="Connection timeout",
    )


@pytest.fixture
def sample_action_result():
    return ActionResult(
        success=True,
        action_type="update",
        device_ip="192.168.1.100",
        message="Update successful",
    )


@pytest.fixture
def sample_failed_action_result():
    return ActionResult(
        success=False,
        action_type="update",
        device_ip="192.168.1.100",
        message="Update failed",
        error="Device unreachable",
    )


@pytest.fixture
def sample_config():
    return {
        "predefined_ips": ["192.168.1.100", "192.168.1.101"],
        "scan_settings": {"timeout": 3.0, "max_workers": 50},
        "update_settings": {"default_channel": "stable"},
    }


@pytest.fixture
def app():
    return create_app()
