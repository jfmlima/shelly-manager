"""
Tests for validation utilities.
"""

from core.utils.validation import is_valid_mac, normalize_mac


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
