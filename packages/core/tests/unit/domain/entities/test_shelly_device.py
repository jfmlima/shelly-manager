from datetime import datetime

import pytest
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status
from pydantic import ValidationError


class TestDiscoveredDevice:

    def test_it_creates_device_with_required_fields(self):
        device = DiscoveredDevice(ip="192.168.1.100", status=Status.DETECTED)

        assert device.ip == "192.168.1.100"
        assert device.status == Status.DETECTED
        assert device.device_id is None
        assert device.device_type is None
        assert device.firmware_version is None
        assert device.device_name is None
        assert device.auth_required is False
        assert device.last_seen is None
        assert device.response_time is None
        assert device.error_message is None
        assert device.has_update is False

    def test_it_creates_device_with_all_fields(self):
        last_seen = datetime.now()
        device = DiscoveredDevice(
            ip="192.168.1.100",
            status=Status.DETECTED,
            device_id="shelly1pm-001",
            device_type="SHPM-1",
            firmware_version="1.14.0",
            device_name="Living Room Switch",
            auth_required=True,
            last_seen=last_seen,
            response_time=0.15,
            error_message=None,
            has_update=True,
        )

        assert device.ip == "192.168.1.100"
        assert device.status == Status.DETECTED
        assert device.device_id == "shelly1pm-001"
        assert device.device_type == "SHPM-1"
        assert device.firmware_version == "1.14.0"
        assert device.device_name == "Living Room Switch"
        assert device.auth_required is True
        assert device.last_seen == last_seen
        assert device.response_time == 0.15
        assert device.error_message is None
        assert device.has_update is True

    def test_it_validates_valid_ip_addresses(self):
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "255.255.255.255",
            "0.0.0.0",
        ]

        for ip in valid_ips:
            device = DiscoveredDevice(ip=ip, status=Status.DETECTED)
            assert device.ip == ip

    def test_it_rejects_invalid_ip_addresses(self):
        invalid_ips = [
            "256.1.1.1",
            "192.168.1",
            "192.168.1.1.1",
            "invalid.ip.address",
            "",
            "192.168.1.-1",
        ]

        for ip in invalid_ips:
            with pytest.raises(ValidationError):
                DiscoveredDevice(ip=ip, status=Status.DETECTED)

    def test_it_validates_response_time_non_negative(self):
        device = DiscoveredDevice(
            ip="192.168.1.100", status=Status.DETECTED, response_time=0.0
        )
        assert device.response_time == 0.0

    def test_it_rejects_negative_response_time(self):
        with pytest.raises(ValidationError):
            DiscoveredDevice(
                ip="192.168.1.100", status=Status.DETECTED, response_time=-0.1
            )

    def test_it_accepts_all_device_statuses(self):
        for status in Status:
            device = DiscoveredDevice(ip="192.168.1.100", status=status)
            assert device.status == status

    def test_it_allows_modification_of_mutable_fields(self):
        device = DiscoveredDevice(
            ip="192.168.1.100",
            status=Status.DETECTED,
            device_name="Original Name",
        )

        device.device_name = "Updated Name"
        device.has_update = True
        device.error_message = "Test error"

        assert device.device_name == "Updated Name"
        assert device.has_update is True
        assert device.error_message == "Test error"

    def test_it_validates_ip_when_modified(self):
        device = DiscoveredDevice(ip="192.168.1.100", status=Status.DETECTED)

        with pytest.raises(ValidationError):
            device.ip = "invalid.ip"

    def test_it_validates_response_time_when_modified(self):
        device = DiscoveredDevice(ip="192.168.1.100", status=Status.DETECTED)

        with pytest.raises(ValidationError):
            device.response_time = -1.0

    def test_it_creates_device_with_minimal_required_data(self):
        device = DiscoveredDevice(ip="10.0.0.1", status=Status.UNREACHABLE)

        assert device.ip == "10.0.0.1"
        assert device.status == Status.UNREACHABLE

    def test_it_handles_auth_required_status(self):
        device = DiscoveredDevice(
            ip="192.168.1.100", status=Status.AUTH_REQUIRED, auth_required=True
        )

        assert device.status == Status.AUTH_REQUIRED
        assert device.auth_required is True

    def test_it_handles_device_with_error_message(self):
        error_msg = "Connection timeout after 5 seconds"
        device = DiscoveredDevice(
            ip="192.168.1.100", status=Status.UNREACHABLE, error_message=error_msg
        )

        assert device.error_message == error_msg
        assert device.status == Status.UNREACHABLE

    def test_it_handles_device_with_firmware_update_available(self):
        device = DiscoveredDevice(
            ip="192.168.1.100",
            status=Status.DETECTED,
            firmware_version="1.13.0",
            has_update=True,
        )

        assert device.firmware_version == "1.13.0"
        assert device.has_update is True

    def test_it_creates_device_with_zero_response_time(self):
        device = DiscoveredDevice(
            ip="192.168.1.100", status=Status.DETECTED, response_time=0.0
        )

        assert device.response_time == 0.0

    def test_it_creates_device_with_high_response_time(self):
        device = DiscoveredDevice(
            ip="192.168.1.100", status=Status.DETECTED, response_time=5.0
        )

        assert device.response_time == 5.0

    def test_it_defaults_boolean_fields_correctly(self):
        device = DiscoveredDevice(ip="192.168.1.100", status=Status.DETECTED)

        assert device.auth_required is False
        assert device.has_update is False

    def test_it_handles_various_device_types(self):
        device_types = ["SHSW-1", "SHPM-1", "SHDM-1", "SHBTN-1", "SHHT-1"]

        for device_type in device_types:
            device = DiscoveredDevice(
                ip="192.168.1.100",
                status=Status.DETECTED,
                device_type=device_type,
            )
            assert device.device_type == device_type

    def test_it_handles_various_firmware_versions(self):
        firmware_versions = ["1.14.0", "20230913-114010/v1.14.0-gcb84623", "2.1.8"]

        for firmware_version in firmware_versions:
            device = DiscoveredDevice(
                ip="192.168.1.100",
                status=Status.DETECTED,
                firmware_version=firmware_version,
            )
            assert device.firmware_version == firmware_version
