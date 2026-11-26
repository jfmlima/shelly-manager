from datetime import datetime

import pytest
from core.domain.value_objects.action_result import ActionResult
from pydantic import ValidationError


class TestActionResult:

    def test_it_creates_action_result_with_required_fields(self):
        result = ActionResult(
            success=True,
            action_type="reboot",
            device_ip="192.168.1.100",
            message="Device rebooted successfully",
        )

        assert result.success is True
        assert result.action_type == "reboot"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Device rebooted successfully"
        assert result.data is None
        assert result.error is None
        assert isinstance(result.timestamp, datetime)

    def test_it_creates_action_result_with_all_fields(self):
        timestamp = datetime.now()
        data = {"old_version": "1.13.0", "new_version": "1.14.0"}

        result = ActionResult(
            success=True,
            action_type="update",
            device_ip="192.168.1.100",
            message="Firmware update completed",
            data=data,
            error=None,
            timestamp=timestamp,
        )

        assert result.success is True
        assert result.action_type == "update"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Firmware update completed"
        assert result.data == data
        assert result.error is None
        assert result.timestamp == timestamp

    def test_it_creates_failed_action_result_with_error(self):
        result = ActionResult(
            success=False,
            action_type="reboot",
            device_ip="192.168.1.100",
            message="Reboot failed",
            error="Device not responding",
        )

        assert result.success is False
        assert result.action_type == "reboot"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Reboot failed"
        assert result.error == "Device not responding"

    def test_it_validates_valid_ip_addresses(self):
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "255.255.255.255",
            "0.0.0.0",
        ]

        for ip in valid_ips:
            result = ActionResult(
                success=True, action_type="test", device_ip=ip, message="Test message"
            )
            assert result.device_ip == ip

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
                ActionResult(
                    success=True,
                    action_type="test",
                    device_ip=ip,
                    message="Test message",
                )

    def test_it_auto_generates_timestamp_when_not_provided(self):
        before_creation = datetime.now()

        result = ActionResult(
            success=True,
            action_type="test",
            device_ip="192.168.1.100",
            message="Test message",
        )

        after_creation = datetime.now()

        assert before_creation <= result.timestamp <= after_creation

    def test_it_accepts_custom_timestamp(self):
        custom_timestamp = datetime(2023, 9, 13, 15, 30, 0)

        result = ActionResult(
            success=True,
            action_type="test",
            device_ip="192.168.1.100",
            message="Test message",
            timestamp=custom_timestamp,
        )

        assert result.timestamp == custom_timestamp
