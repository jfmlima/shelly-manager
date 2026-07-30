"""
Tests for validation utilities.
"""

import pytest
from core.utils.validation import (
    is_valid_mac,
    normalize_mac,
    validate_ip_address,
    validate_ip_address_list,
    validate_mac,
)


class TestNormalizeMac:
    def test_it_normalizes_mac_with_colons(self):
        result = normalize_mac("AA:BB:CC:DD:EE:FF")
        assert result == "AABBCCDDEEFF"

    def test_it_normalizes_mac_with_dashes(self):
        result = normalize_mac("AA-BB-CC-DD-EE-FF")
        assert result == "AABBCCDDEEFF"

    def test_it_normalizes_lowercase_mac(self):
        result = normalize_mac("aa:bb:cc:dd:ee:ff")
        assert result == "AABBCCDDEEFF"

    def test_it_normalizes_already_normalized_mac(self):
        result = normalize_mac("AABBCCDDEEFF")
        assert result == "AABBCCDDEEFF"

    def test_it_normalizes_mixed_case_mac(self):
        result = normalize_mac("Aa:Bb:Cc:Dd:Ee:Ff")
        assert result == "AABBCCDDEEFF"

    def test_it_normalizes_mac_with_mixed_separators(self):
        result = normalize_mac("AA:BB-CC:DD-EE:FF")
        assert result == "AABBCCDDEEFF"

    def test_it_preserves_special_global_mac(self):
        result = normalize_mac("*")
        assert result == "*"

    def test_it_handles_empty_string(self):
        result = normalize_mac("")
        assert result == ""


class TestIsValidMac:
    def test_it_validates_mac_with_colons(self):
        assert is_valid_mac("AA:BB:CC:DD:EE:FF") is True

    def test_it_validates_mac_with_dashes(self):
        assert is_valid_mac("AA-BB-CC-DD-EE-FF") is True

    def test_it_validates_mac_without_separators(self):
        assert is_valid_mac("AABBCCDDEEFF") is True

    def test_it_validates_lowercase_mac(self):
        assert is_valid_mac("aa:bb:cc:dd:ee:ff") is True

    def test_it_validates_mixed_case_mac(self):
        assert is_valid_mac("Aa:Bb:Cc:Dd:Ee:Ff") is True

    def test_it_validates_global_fallback_mac(self):
        assert is_valid_mac("*") is True

    def test_it_rejects_invalid_mac_too_short(self):
        assert is_valid_mac("AABBCCDDEE") is False

    def test_it_rejects_invalid_mac_too_long(self):
        assert is_valid_mac("AABBCCDDEEFF00") is False

    def test_it_rejects_invalid_mac_with_invalid_chars(self):
        assert is_valid_mac("GGHHIIJJKKLL") is False

    def test_it_rejects_empty_string(self):
        assert is_valid_mac("") is False

    def test_it_rejects_random_string(self):
        assert is_valid_mac("not-a-mac") is False

    def test_it_rejects_ip_address(self):
        assert is_valid_mac("192.168.1.1") is False


class TestValidateMac:
    def test_it_normalizes_a_valid_mac(self):
        assert validate_mac("aa:bb:cc:dd:ee:ff") == "AABBCCDDEEFF"

    def test_it_raises_on_an_invalid_mac(self):
        with pytest.raises(ValueError):
            validate_mac("not-a-mac")

    def test_it_rejects_the_wildcard_by_default(self):
        with pytest.raises(ValueError):
            validate_mac("*")

    def test_it_passes_the_wildcard_through_when_allowed(self):
        assert validate_mac("*", allow_wildcard=True) == "*"


class TestValidateIpAddress:
    def test_it_returns_a_valid_ip(self):
        assert validate_ip_address("192.168.1.10") == "192.168.1.10"

    def test_it_raises_on_an_invalid_ip(self):
        with pytest.raises(ValueError):
            validate_ip_address("not-an-ip")

    def test_it_validates_a_list(self):
        ips = ["192.168.1.10", "10.0.0.1"]
        assert validate_ip_address_list(ips) == ips

    def test_it_raises_on_an_invalid_ip_in_a_list(self):
        with pytest.raises(ValueError):
            validate_ip_address_list(["192.168.1.10", "bad"])
