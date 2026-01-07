from time import time

from core.utils.validation import normalize_mac

# Default TTL of 1 hour for auth state entries
DEFAULT_TTL_SECONDS = 3600


class AuthStateCache:
    """
    In-memory cache for device authentication requirements.
    Keyed by MAC address or IP address.

    Entries expire after a configurable TTL to prevent stale auth state
    and allow the cache to be cleaned up over time.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._auth_required: dict[str, tuple[bool, float]] = {}
        self._ttl = ttl_seconds

    def _normalize_id(self, device_id: str) -> str:
        """Normalize MAC or IP address."""
        return normalize_mac(device_id)

    def mark_auth_required(self, device_id: str) -> None:
        """Mark a device as requiring authentication."""
        normalized = self._normalize_id(device_id)
        self._auth_required[normalized] = (True, time())

    def mark_auth_not_required(self, device_id: str) -> None:
        """Mark a device as NOT requiring authentication."""
        normalized = self._normalize_id(device_id)
        self._auth_required[normalized] = (False, time())

    def requires_auth(self, device_id: str) -> bool:
        """Check if a device is known to require authentication."""
        normalized = self._normalize_id(device_id)
        entry = self._auth_required.get(normalized)
        if entry is None:
            return False

        value, timestamp = entry
        if time() - timestamp > self._ttl:
            # Entry has expired, remove it
            del self._auth_required[normalized]
            return False

        return value

    def is_known(self, device_id: str) -> bool:
        """Check if we have auth info for this device (not expired)."""
        normalized = self._normalize_id(device_id)
        entry = self._auth_required.get(normalized)
        if entry is None:
            return False

        _, timestamp = entry
        if time() - timestamp > self._ttl:
            # Entry has expired, remove it
            del self._auth_required[normalized]
            return False

        return True

    def clear(self) -> None:
        """Clear the cache."""
        self._auth_required.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        current_time = time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._auth_required.items()
            if current_time - timestamp > self._ttl
        ]
        for key in expired_keys:
            del self._auth_required[key]
        return len(expired_keys)

    def __len__(self) -> int:
        """Return the number of entries in the cache (including expired)."""
        return len(self._auth_required)
