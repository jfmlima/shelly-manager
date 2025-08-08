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

    def test_it_handles_various_action_types(self):
        action_types = ["reboot", "update", "config-set", "scan", "status-check"]

        for action_type in action_types:
            result = ActionResult(
                success=True,
                action_type=action_type,
                device_ip="192.168.1.100",
                message=f"{action_type} completed",
            )
            assert result.action_type == action_type

    def test_it_handles_complex_data_payload(self):
        complex_data = {
            "firmware": {
                "old_version": "1.13.0",
                "new_version": "1.14.0",
                "size": 512000,
            },
            "device_info": {"type": "SHPM-1", "mac": "AA:BB:CC:DD:EE:FF"},
            "metrics": {"download_time": 30.5, "install_time": 45.2},
        }

        result = ActionResult(
            success=True,
            action_type="update",
            device_ip="192.168.1.100",
            message="Complex update completed",
            data=complex_data,
        )

        assert result.data == complex_data
        assert result.data["firmware"]["old_version"] == "1.13.0"
        assert result.data["metrics"]["download_time"] == 30.5

    def test_it_handles_empty_data_payload(self):
        result = ActionResult(
            success=True,
            action_type="reboot",
            device_ip="192.168.1.100",
            message="Reboot completed",
            data={},
        )

        assert result.data == {}

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

    def test_it_handles_long_error_messages(self):
        long_error = "A" * 1000

        result = ActionResult(
            success=False,
            action_type="update",
            device_ip="192.168.1.100",
            message="Update failed",
            error=long_error,
        )

        assert result.error == long_error
        assert len(result.error) == 1000

    def test_it_handles_long_messages(self):
        long_message = "Operation completed with extensive details: " + "B" * 500

        result = ActionResult(
            success=True,
            action_type="config-set",
            device_ip="192.168.1.100",
            message=long_message,
        )

        assert result.message == long_message

    def test_it_handles_successful_result_with_warning_message(self):
        result = ActionResult(
            success=True,
            action_type="update",
            device_ip="192.168.1.100",
            message="Update completed with warnings",
            error="Non-critical issue detected",
        )

        assert result.success is True
        assert "warnings" in result.message
        assert result.error == "Non-critical issue detected"

    def test_it_creates_result_with_numeric_data(self):
        numeric_data = {
            "temperature": 45.7,
            "uptime": 3600,
            "memory_usage": 85.5,
            "cpu_load": 12,
        }

        result = ActionResult(
            success=True,
            action_type="status-check",
            device_ip="192.168.1.100",
            message="Status check completed",
            data=numeric_data,
        )

        assert result.data == numeric_data
        assert result.data["temperature"] == 45.7
        assert result.data["uptime"] == 3600

    def test_it_creates_result_with_boolean_data(self):
        boolean_data = {
            "wifi_connected": True,
            "mqtt_enabled": False,
            "cloud_connected": True,
            "update_available": False,
        }

        result = ActionResult(
            success=True,
            action_type="status-check",
            device_ip="192.168.1.100",
            message="Status check completed",
            data=boolean_data,
        )

        assert result.data == boolean_data
        assert result.data["wifi_connected"] is True
        assert result.data["mqtt_enabled"] is False

    def test_it_creates_result_with_mixed_data_types(self):
        mixed_data = {
            "string_value": "test",
            "int_value": 42,
            "float_value": 3.14,
            "bool_value": True,
            "list_value": [1, 2, 3],
            "nested_dict": {"key": "value"},
        }

        result = ActionResult(
            success=True,
            action_type="test",
            device_ip="192.168.1.100",
            message="Mixed data test",
            data=mixed_data,
        )

        assert result.data == mixed_data
        assert result.data["string_value"] == "test"
        assert result.data["nested_dict"]["key"] == "value"
