from core.domain.services.validation_service import ValidationService


class TestValidationService:

    def test_it_validates_valid_ip_address(self):
        result = ValidationService.validate_ip_address("192.168.1.1")

        assert result is True

    def test_it_validates_valid_ip_address_with_zeros(self):
        result = ValidationService.validate_ip_address("192.168.1.0")

        assert result is True

    def test_it_validates_valid_ip_address_with_max_values(self):
        result = ValidationService.validate_ip_address("255.255.255.255")

        assert result is True

    def test_it_rejects_invalid_ip_address_format(self):
        result = ValidationService.validate_ip_address("invalid.ip.address")

        assert result is False

    def test_it_rejects_ip_address_with_out_of_range_values(self):
        result = ValidationService.validate_ip_address("256.1.1.1")

        assert result is False

    def test_it_rejects_ip_address_with_missing_octets(self):
        result = ValidationService.validate_ip_address("192.168.1")

        assert result is False

    def test_it_rejects_empty_ip_address(self):
        result = ValidationService.validate_ip_address("")

        assert result is False

    def test_it_rejects_none_ip_address(self):
        result = ValidationService.validate_ip_address(None)

        assert result is False

    def test_it_validates_valid_device_credentials_both_provided(self):
        result = ValidationService.validate_device_credentials("admin", "password123")

        assert result is True

    def test_it_validates_valid_device_credentials_both_none(self):
        result = ValidationService.validate_device_credentials(None, None)

        assert result is True

    def test_it_rejects_credentials_with_only_username(self):
        result = ValidationService.validate_device_credentials("admin", None)

        assert result is False

    def test_it_rejects_credentials_with_only_password(self):
        result = ValidationService.validate_device_credentials(None, "password123")

        assert result is False

    def test_it_accepts_credentials_with_empty_username(self):
        result = ValidationService.validate_device_credentials("", "password123")

        assert result is True

    def test_it_accepts_credentials_with_empty_password(self):
        result = ValidationService.validate_device_credentials("admin", "")

        assert result is True

    def test_it_accepts_credentials_with_both_empty(self):
        result = ValidationService.validate_device_credentials("", "")

        assert result is True

    def test_it_validates_valid_scan_range_ascending(self):
        result = ValidationService.validate_scan_range("192.168.1.1", "192.168.1.10")

        assert result is True

    def test_it_validates_valid_scan_range_same_ip(self):
        result = ValidationService.validate_scan_range("192.168.1.1", "192.168.1.1")

        assert result is True

    def test_it_validates_scan_range_across_subnets(self):
        result = ValidationService.validate_scan_range("192.168.1.255", "192.168.2.1")

        assert result is True

    def test_it_rejects_scan_range_with_start_greater_than_end(self):
        result = ValidationService.validate_scan_range("192.168.1.10", "192.168.1.1")

        assert result is False

    def test_it_rejects_scan_range_with_invalid_start_ip(self):
        result = ValidationService.validate_scan_range("invalid.ip", "192.168.1.10")

        assert result is False

    def test_it_rejects_scan_range_with_invalid_end_ip(self):
        result = ValidationService.validate_scan_range("192.168.1.1", "invalid.ip")

        assert result is False

    def test_it_rejects_scan_range_with_both_invalid_ips(self):
        result = ValidationService.validate_scan_range("invalid.start", "invalid.end")

        assert result is False

    def test_it_validates_scan_range_with_min_max_values(self):
        result = ValidationService.validate_scan_range("0.0.0.0", "255.255.255.255")

        assert result is True
