"""
Tests for API request models and validation.
"""

import pytest
from api.presentation.dto.requests import CredentialCreateRequest
from pydantic import ValidationError


class TestCredentialCreateRequest:
    def test_it_creates_request_with_valid_mac(self):
        request = CredentialCreateRequest(
            mac="AA:BB:CC:DD:EE:FF",
            username="admin",
            password="secret123",
        )

        # MAC should be normalized
        assert request.mac == "AABBCCDDEEFF"
        assert request.username == "admin"
        assert request.password == "secret123"

    def test_it_normalizes_mac_with_colons(self):
        request = CredentialCreateRequest(
            mac="aa:bb:cc:dd:ee:ff",
            password="secret",
        )

        assert request.mac == "AABBCCDDEEFF"

    def test_it_normalizes_mac_with_dashes(self):
        request = CredentialCreateRequest(
            mac="AA-BB-CC-DD-EE-FF",
            password="secret",
        )

        assert request.mac == "AABBCCDDEEFF"

    def test_it_accepts_mac_without_separators(self):
        request = CredentialCreateRequest(
            mac="AABBCCDDEEFF",
            password="secret",
        )

        assert request.mac == "AABBCCDDEEFF"

    def test_it_accepts_global_fallback_mac(self):
        request = CredentialCreateRequest(
            mac="*",
            password="globalpass",
        )

        assert request.mac == "*"

    def test_it_defaults_username_to_admin(self):
        request = CredentialCreateRequest(
            mac="AABBCCDDEEFF",
            password="secret",
        )

        assert request.username == "admin"

    def test_it_rejects_invalid_mac_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreateRequest(
                mac="AABBCCDDEE",
                password="secret",
            )

        errors = exc_info.value.errors()
        assert any("mac" in str(e.get("loc", "")) for e in errors)

    def test_it_rejects_invalid_mac_too_long(self):
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreateRequest(
                mac="AABBCCDDEEFF00",
                password="secret",
            )

        errors = exc_info.value.errors()
        assert any("mac" in str(e.get("loc", "")) for e in errors)

    def test_it_rejects_invalid_mac_with_invalid_chars(self):
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreateRequest(
                mac="GGHHIIJJKKLL",
                password="secret",
            )

        errors = exc_info.value.errors()
        assert any("mac" in str(e.get("loc", "")) for e in errors)

    def test_it_rejects_random_string_as_mac(self):
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreateRequest(
                mac="not-a-valid-mac",
                password="secret",
            )

        errors = exc_info.value.errors()
        assert any("mac" in str(e.get("loc", "")) for e in errors)

    def test_it_rejects_empty_mac(self):
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreateRequest(
                mac="",
                password="secret",
            )

        errors = exc_info.value.errors()
        assert any("mac" in str(e.get("loc", "")) for e in errors)

    def test_it_requires_password(self):
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreateRequest(
                mac="AABBCCDDEEFF",
            )

        errors = exc_info.value.errors()
        assert any("password" in str(e.get("loc", "")) for e in errors)

    def test_it_rejects_empty_password(self):
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreateRequest(
                mac="AABBCCDDEEFF",
                password="",
            )

        errors = exc_info.value.errors()
        assert any("password" in str(e.get("loc", "")) for e in errors)

    def test_it_accepts_custom_username(self):
        request = CredentialCreateRequest(
            mac="AABBCCDDEEFF",
            username="customuser",
            password="secret",
        )

        assert request.username == "customuser"

    def test_it_provides_helpful_error_message_for_invalid_mac(self):
        with pytest.raises(ValidationError) as exc_info:
            CredentialCreateRequest(
                mac="invalid",
                password="secret",
            )

        error_message = str(exc_info.value)
        assert (
            "Invalid MAC address format" in error_message
            or "mac" in error_message.lower()
        )
