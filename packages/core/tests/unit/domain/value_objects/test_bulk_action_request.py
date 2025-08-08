import pytest
from core.domain.value_objects.bulk_action_request import BulkActionRequest
from pydantic import ValidationError


class TestBulkActionRequest:

    def test_it_creates_bulk_action_request_with_required_fields(self):
        request = BulkActionRequest(
            action_type="reboot", device_ips=["192.168.1.100", "192.168.1.101"]
        )

        assert request.action_type == "reboot"
        assert request.device_ips == ["192.168.1.100", "192.168.1.101"]
        assert request.parameters == {}

    def test_it_creates_bulk_action_request_with_parameters(self):
        parameters = {"force": True, "timeout": 30}
        request = BulkActionRequest(
            action_type="update", device_ips=["192.168.1.100"], parameters=parameters
        )

        assert request.action_type == "update"
        assert request.device_ips == ["192.168.1.100"]
        assert request.parameters == parameters

    def test_it_validates_valid_action_types(self):
        valid_actions = ["update", "reboot", "config-set"]

        for action in valid_actions:
            request = BulkActionRequest(
                action_type=action, device_ips=["192.168.1.100"]
            )
            assert request.action_type == action

    def test_it_rejects_invalid_action_types(self):
        invalid_actions = ["invalid", "delete", "scan", "status"]

        for action in invalid_actions:
            with pytest.raises(ValidationError, match="Invalid bulk action type"):
                BulkActionRequest(action_type=action, device_ips=["192.168.1.100"])

    def test_it_validates_valid_ip_addresses(self):
        valid_ips = [
            ["192.168.1.1"],
            ["10.0.0.1", "172.16.0.1"],
            ["255.255.255.255", "0.0.0.0", "127.0.0.1"],
        ]

        for ip_list in valid_ips:
            request = BulkActionRequest(action_type="reboot", device_ips=ip_list)
            assert request.device_ips == ip_list

    def test_it_rejects_invalid_ip_addresses(self):
        invalid_ip_lists = [
            ["256.1.1.1"],
            ["192.168.1.100", "invalid.ip"],
            ["192.168.1"],
            ["192.168.1.1.1"],
            [""],
        ]

        for ip_list in invalid_ip_lists:
            with pytest.raises(ValidationError):
                BulkActionRequest(action_type="reboot", device_ips=ip_list)

    def test_it_rejects_empty_device_ips_list(self):
        with pytest.raises(ValidationError):
            BulkActionRequest(action_type="reboot", device_ips=[])

    def test_it_handles_single_device_ip(self):
        request = BulkActionRequest(action_type="reboot", device_ips=["192.168.1.100"])

        assert len(request.device_ips) == 1
        assert request.device_ips[0] == "192.168.1.100"

    def test_it_handles_multiple_device_ips(self):
        ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102", "10.0.0.1"]
        request = BulkActionRequest(action_type="update", device_ips=ips)

        assert len(request.device_ips) == 4
        assert request.device_ips == ips

    def test_it_handles_complex_parameters(self):
        complex_params = {
            "config": {
                "wifi": {"ssid": "NewNetwork", "password": "newpassword"},
                "mqtt": {"enable": True, "server": "192.168.1.50"},
            },
            "force": True,
            "timeout": 60,
        }
        request = BulkActionRequest(
            action_type="config-set",
            device_ips=["192.168.1.100"],
            parameters=complex_params,
        )

        assert request.parameters == complex_params
        assert request.parameters["config"]["wifi"]["ssid"] == "NewNetwork"
        assert request.parameters["force"] is True

    def test_it_handles_empty_parameters(self):
        request = BulkActionRequest(
            action_type="reboot", device_ips=["192.168.1.100"], parameters={}
        )

        assert request.parameters == {}

    def test_it_defaults_parameters_to_empty_dict(self):
        request = BulkActionRequest(action_type="reboot", device_ips=["192.168.1.100"])

        assert request.parameters == {}

    def test_it_handles_string_parameters(self):
        params = {
            "channel": "beta",
            "reason": "Scheduled maintenance",
            "notification": "Device will reboot in 30 seconds",
        }
        request = BulkActionRequest(
            action_type="update", device_ips=["192.168.1.100"], parameters=params
        )

        assert request.parameters == params
        assert request.parameters["channel"] == "beta"

    def test_it_handles_numeric_parameters(self):
        params = {"timeout": 30, "retry_count": 3, "delay": 5.5}
        request = BulkActionRequest(
            action_type="reboot", device_ips=["192.168.1.100"], parameters=params
        )

        assert request.parameters == params
        assert request.parameters["timeout"] == 30
        assert request.parameters["delay"] == 5.5

    def test_it_handles_boolean_parameters(self):
        params = {"force": True, "backup_config": False, "notify_completion": True}
        request = BulkActionRequest(
            action_type="config-set", device_ips=["192.168.1.100"], parameters=params
        )

        assert request.parameters == params
        assert request.parameters["force"] is True
        assert request.parameters["backup_config"] is False

    def test_it_handles_list_parameters(self):
        params = {
            "excluded_settings": ["wifi", "mqtt"],
            "notification_emails": ["admin@example.com", "ops@example.com"],
        }
        request = BulkActionRequest(
            action_type="config-set", device_ips=["192.168.1.100"], parameters=params
        )

        assert request.parameters == params
        assert request.parameters["excluded_settings"] == ["wifi", "mqtt"]

    def test_it_validates_large_device_list(self):
        large_ip_list = [f"192.168.1.{i}" for i in range(1, 101)]
        request = BulkActionRequest(action_type="reboot", device_ips=large_ip_list)

        assert len(request.device_ips) == 100
        assert request.device_ips[0] == "192.168.1.1"
        assert request.device_ips[-1] == "192.168.1.100"

    def test_it_handles_mixed_subnet_device_ips(self):
        mixed_ips = ["192.168.1.100", "10.0.0.1", "172.16.0.1", "127.0.0.1"]
        request = BulkActionRequest(action_type="update", device_ips=mixed_ips)

        assert request.device_ips == mixed_ips

    def test_it_validates_duplicate_ip_addresses(self):
        duplicate_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.100"]
        request = BulkActionRequest(action_type="reboot", device_ips=duplicate_ips)

        assert request.device_ips == duplicate_ips

    def test_it_rejects_mixed_valid_and_invalid_ips(self):
        mixed_ips = ["192.168.1.100", "invalid.ip", "192.168.1.101"]

        with pytest.raises(ValidationError):
            BulkActionRequest(action_type="reboot", device_ips=mixed_ips)
