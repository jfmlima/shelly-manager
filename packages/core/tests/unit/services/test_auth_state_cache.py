from unittest.mock import patch

import pytest
from core.services.auth_state_cache import DEFAULT_TTL_SECONDS, AuthStateCache


class TestAuthStateCache:
    @pytest.fixture
    def cache(self):
        return AuthStateCache()

    @pytest.fixture
    def cache_with_short_ttl(self):
        return AuthStateCache(ttl_seconds=1)

    def test_it_creates_cache_with_default_ttl(self, cache):
        assert cache._ttl == DEFAULT_TTL_SECONDS

    def test_it_creates_cache_with_custom_ttl(self):
        cache = AuthStateCache(ttl_seconds=60)
        assert cache._ttl == 60

    def test_it_marks_device_as_auth_required(self, cache):
        cache.mark_auth_required("AABBCCDDEEFF")

        assert cache.requires_auth("AABBCCDDEEFF") is True

    def test_it_marks_device_as_not_auth_required(self, cache):
        cache.mark_auth_required("AABBCCDDEEFF")
        cache.mark_auth_not_required("AABBCCDDEEFF")

        assert cache.requires_auth("AABBCCDDEEFF") is False

    def test_it_returns_false_for_unknown_device(self, cache):
        assert cache.requires_auth("UNKNOWN") is False

    def test_it_normalizes_mac_with_colons(self, cache):
        cache.mark_auth_required("AA:BB:CC:DD:EE:FF")

        assert cache.requires_auth("AABBCCDDEEFF") is True
        assert cache.requires_auth("aa:bb:cc:dd:ee:ff") is True

    def test_it_normalizes_mac_with_dashes(self, cache):
        cache.mark_auth_required("AA-BB-CC-DD-EE-FF")

        assert cache.requires_auth("AABBCCDDEEFF") is True

    def test_it_normalizes_lowercase_mac(self, cache):
        cache.mark_auth_required("aabbccddeeff")

        assert cache.requires_auth("AABBCCDDEEFF") is True

    def test_it_reports_device_as_known_after_marking(self, cache):
        cache.mark_auth_required("AABBCCDDEEFF")

        assert cache.is_known("AABBCCDDEEFF") is True

    def test_it_reports_unknown_device_as_not_known(self, cache):
        assert cache.is_known("UNKNOWN") is False

    def test_it_clears_all_entries(self, cache):
        cache.mark_auth_required("DEVICE1")
        cache.mark_auth_required("DEVICE2")

        cache.clear()

        assert cache.is_known("DEVICE1") is False
        assert cache.is_known("DEVICE2") is False
        assert len(cache) == 0

    def test_it_returns_length_of_cache(self, cache):
        assert len(cache) == 0

        cache.mark_auth_required("DEVICE1")
        cache.mark_auth_required("DEVICE2")

        assert len(cache) == 2

    def test_it_expires_entry_after_ttl(self):
        # Use very short TTL and control time via patching
        with patch("core.services.auth_state_cache.time") as mock_time:
            mock_time.return_value = 1000000
            cache = AuthStateCache(ttl_seconds=1)
            cache.mark_auth_required("AABBCCDDEEFF")

            # Entry should exist immediately
            assert cache.requires_auth("AABBCCDDEEFF") is True

            # Simulate time passing beyond TTL
            mock_time.return_value = 1000000 + 2  # 2 seconds later (TTL is 1)

            # Entry should be expired
            assert cache.requires_auth("AABBCCDDEEFF") is False

    def test_it_removes_expired_entry_on_access(self):
        with patch("core.services.auth_state_cache.time") as mock_time:
            mock_time.return_value = 1000000
            cache = AuthStateCache(ttl_seconds=1)
            cache.mark_auth_required("AABBCCDDEEFF")

            mock_time.return_value = 1000000 + 2

            # Access should remove expired entry
            cache.requires_auth("AABBCCDDEEFF")

            # Entry should be gone
            assert "AABBCCDDEEFF" not in cache._auth_required

    def test_is_known_removes_expired_entry(self):
        with patch("core.services.auth_state_cache.time") as mock_time:
            mock_time.return_value = 1000000
            cache = AuthStateCache(ttl_seconds=1)
            cache.mark_auth_required("AABBCCDDEEFF")

            mock_time.return_value = 1000000 + 2

            assert cache.is_known("AABBCCDDEEFF") is False
            assert "AABBCCDDEEFF" not in cache._auth_required

    def test_it_refreshes_timestamp_on_update(self):
        initial_time = 1000000

        with patch("core.services.auth_state_cache.time") as mock_time:
            mock_time.return_value = initial_time
            cache = AuthStateCache()
            cache.mark_auth_required("AABBCCDDEEFF")

            # Update timestamp
            mock_time.return_value = initial_time + 1800  # 30 minutes later
            cache.mark_auth_required("AABBCCDDEEFF")

            # Check timestamp was updated
            _, timestamp = cache._auth_required["AABBCCDDEEFF"]
            assert timestamp == initial_time + 1800

    def test_cleanup_expired_removes_old_entries(self):
        with patch("core.services.auth_state_cache.time") as mock_time:
            mock_time.return_value = 1000000
            cache = AuthStateCache(ttl_seconds=1)
            cache.mark_auth_required("OLD_DEVICE")

            mock_time.return_value = 1000000 + 0.5  # Before TTL
            cache.mark_auth_required("NEW_DEVICE")

            mock_time.return_value = 1000000 + 2  # After TTL for first device
            removed = cache.cleanup_expired()

            assert removed == 1
            assert "OLD_DEVICE" not in cache._auth_required
            assert "NEW_DEVICE" not in cache._auth_required  # Also expired by now

    def test_cleanup_expired_returns_zero_when_no_expired(self, cache):
        cache.mark_auth_required("DEVICE1")
        cache.mark_auth_required("DEVICE2")

        removed = cache.cleanup_expired()

        assert removed == 0
        assert len(cache) == 2

    def test_it_handles_ip_addresses(self, cache):
        cache.mark_auth_required("192.168.1.100")

        assert cache.requires_auth("192.168.1.100") is True
        assert cache.is_known("192.168.1.100") is True


class TestDefaultTTL:
    def test_default_ttl_is_one_hour(self):
        assert DEFAULT_TTL_SECONDS == 3600
