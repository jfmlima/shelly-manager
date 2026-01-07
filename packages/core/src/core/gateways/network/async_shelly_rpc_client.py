import logging
import time
import uuid
from typing import Any

import httpx
from httpx._client import UseClientDefault
from httpx._types import AuthTypes

from core.domain.entities.exceptions import (
    DeviceAuthenticationError,
    DeviceCommunicationError,
)
from core.services.auth_state_cache import AuthStateCache
from core.services.authentication_service import AuthenticationService
from core.utils.validation import normalize_mac

from .network import RpcNetworkGateway

logger = logging.getLogger(__name__)


class AsyncShellyRPCClient(RpcNetworkGateway):

    def __init__(
        self,
        session: httpx.AsyncClient | None = None,
        timeout: int = 3,
        verify: bool | None = None,
        authentication_service: AuthenticationService | None = None,
        auth_state_cache: AuthStateCache | None = None,
    ):
        self.timeout = timeout
        self._session = session or httpx.AsyncClient(
            timeout=timeout, verify=True if verify is None else verify
        )
        self.authentication_service = authentication_service
        self.auth_state_cache = auth_state_cache
        self._closed = False
        self._ip_to_mac: dict[str, str] = {}
        self._digest_auth_cache: dict[str, httpx.DigestAuth] = {}

    async def make_rpc_request(
        self,
        ip: str,
        method: str,
        params: dict[str, Any] | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float = 3.0,
    ) -> tuple[dict[str, Any], float]:
        """Make an RPC request to a Shelly device.

        Args:
            ip: Device IP address
            method: RPC method name
            params: Optional method parameters
            auth: Optional explicit auth credentials (username, password)
            timeout: Request timeout in seconds

        Returns:
            Tuple of (response_data, elapsed_time)

        Raises:
            Exception: On network errors or authentication failures
        """
        start_total_time = time.time()  # Capture start time for total duration
        url = f"http://{ip}/rpc"
        payload: dict[str, Any] = {"id": str(uuid.uuid4()), "method": method}
        if params:
            payload["params"] = params

        headers = {"Content-Type": "application/json"}

        # Resolve authentication
        req_auth = await self._resolve_authentication(ip, auth, timeout)

        # Execute request
        response, _ = await self._execute_http_request(
            url, payload, headers, timeout=timeout, auth=req_auth
        )

        # Handle 401 authentication challenge
        if response.status_code == 401:
            response = await self._handle_auth_challenge(
                ip, url, payload, headers, timeout, had_auth=req_auth is not None
            )

        # Calculate total response time after all attempts
        response_time = time.time() - start_total_time

        # Return successful response
        if response.status_code == 200:
            return response.json(), response_time

        raise DeviceCommunicationError(
            ip, f"HTTP {response.status_code}: {response.text}"
        )

    def _normalize_id(self, device_id: str) -> str:
        """Helper to ensure ID is normalized (uppercase, no colons)."""
        return normalize_mac(device_id)

    async def _resolve_authentication(
        self, ip: str, explicit_auth: tuple[str, str] | None, timeout: float
    ) -> httpx.Auth | None:
        """Resolve authentication for a device request.

        Args:
            ip: Device IP address
            explicit_auth: Explicit credentials tuple (username, password) or None
            timeout: Request timeout

        Returns:
            httpx.Auth instance or None
        """
        if explicit_auth:
            return httpx.BasicAuth(username=explicit_auth[0], password=explicit_auth[1])

        if self.authentication_service is None or self.auth_state_cache is None:
            return None

        normalized_ip = self._normalize_id(ip)
        known_mac = self._ip_to_mac.get(normalized_ip)

        # Check if IP or known MAC requires auth
        if not (
            self.auth_state_cache.requires_auth(normalized_ip)
            or (known_mac and self.auth_state_cache.requires_auth(known_mac))
        ):
            return None

        # Resolve MAC and get/create DigestAuth
        mac = await self._ensure_mac(ip, timeout)
        if mac:
            return await self._get_or_create_digest_auth(ip, mac)

        return None

    async def _get_or_create_digest_auth(
        self, ip: str, mac: str
    ) -> httpx.DigestAuth | None:
        """Get cached or create new DigestAuth instance for a device.

        Args:
            ip: Device IP address
            mac: Device MAC address (already normalized)

        Returns:
            DigestAuth instance or None
        """
        if self.authentication_service is None:
            return None

        # Try to reuse cached DigestAuth instance (thread-safe with dict.get)
        cached_auth = self._digest_auth_cache.get(mac)
        if cached_auth is not None:
            logger.debug("Reusing DigestAuth for %s (MAC: %s)", ip, mac)
            return cached_auth

        # Create new DigestAuth
        credential = await self.authentication_service.resolve_credentials(mac)
        if not credential:
            return None

        logger.debug("Creating new DigestAuth for %s (MAC: %s)", ip, mac)
        digest_auth = httpx.DigestAuth(
            username=credential.username, password=credential.password
        )
        self._digest_auth_cache[mac] = digest_auth
        return digest_auth

    async def _execute_http_request(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        auth: httpx.Auth | None = None,
        timeout: float = 3.0,
    ) -> tuple[httpx.Response, float]:
        """Execute HTTP POST request and track timing.

        Args:
            url: Request URL
            payload: JSON payload
            headers: HTTP headers
            auth: Authentication instance
            timeout: Request timeout

        Returns:
            Tuple of (response, elapsed_time)
        """
        start_time = time.time()
        auth_param: AuthTypes | UseClientDefault = (
            auth if auth is not None else httpx.USE_CLIENT_DEFAULT
        )
        try:
            response = await self._session.post(
                url,
                json=payload,
                headers=headers,
                auth=auth_param,
                timeout=timeout,
            )
            elapsed = time.time() - start_time
            return response, elapsed
        except httpx.RequestError as e:
            elapsed = time.time() - start_time
            # Extract IP from URL for error context
            ip = url.replace("http://", "").replace("/rpc", "")
            raise DeviceCommunicationError(ip, str(e)) from e

    def _invalidate_auth_cache(self, ip: str) -> None:
        """Invalidate authentication cache for a device.

        Args:
            ip: Device IP address
        """
        normalized_ip = self._normalize_id(ip)

        if self.auth_state_cache:
            self.auth_state_cache.mark_auth_not_required(normalized_ip)

        mac = self._ip_to_mac.get(normalized_ip)
        if mac:
            if self.auth_state_cache:
                self.auth_state_cache.mark_auth_not_required(mac)
            if mac in self._digest_auth_cache:
                del self._digest_auth_cache[mac]

    async def _handle_auth_challenge(
        self,
        ip: str,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
        had_auth: bool,
    ) -> httpx.Response:
        """Handle 401 authentication challenge and retry.

        Args:
            ip: Device IP address
            url: Request URL
            payload: JSON payload
            headers: HTTP headers
            timeout: Request timeout
            had_auth: Whether the original request included auth

        Returns:
            Response from retry attempt

        Raises:
            Exception if authentication fails
        """
        if had_auth:
            # If we already had auth and still got 401, it's a real failure
            logger.warning("Authentication failed for %s even with credentials", ip)
            self._invalidate_auth_cache(ip)
            raise DeviceAuthenticationError(
                ip, "Authentication failed with stored credentials"
            )

        # First 401 - it's a challenge
        logger.debug("Received auth challenge from %s", ip)
        if self.authentication_service is None or self.auth_state_cache is None:
            raise DeviceAuthenticationError(
                ip,
                "Device requires authentication but no authentication service is configured",
            )

        # Mark as requiring auth
        normalized_ip = self._normalize_id(ip)
        self.auth_state_cache.mark_auth_required(normalized_ip)

        # Resolve MAC and credentials
        mac = await self._ensure_mac(ip, timeout)
        if not mac:
            raise DeviceAuthenticationError(
                ip, "Could not resolve device MAC address for credential lookup"
            )

        normalized_mac = self._normalize_id(mac)
        self.auth_state_cache.mark_auth_required(normalized_mac)

        # Get or create DigestAuth
        digest_auth = await self._get_or_create_digest_auth(ip, normalized_mac)
        if not digest_auth:
            raise DeviceAuthenticationError(ip, "No credentials stored for this device")

        # Retry with authentication
        logger.debug("Retrying with DigestAuth for %s", mac)
        response = await self._session.post(
            url,
            json=payload,
            headers=headers,
            auth=digest_auth,
            timeout=timeout,
        )

        if response.status_code == 401:
            logger.warning("Authentication failed on retry for %s", ip)
            raise DeviceAuthenticationError(ip, "Invalid credentials for device")

        return response

    async def _ensure_mac(self, ip: str, timeout: float) -> str | None:
        """Get or resolve MAC address for an IP."""
        normalized_ip = self._normalize_id(ip)
        if normalized_ip in self._ip_to_mac:
            return self._ip_to_mac[normalized_ip]

        mac = await self._get_mac_address(ip, timeout)
        if mac:
            normalized_mac = self._normalize_id(mac)
            self._ip_to_mac[normalized_ip] = normalized_mac
            return normalized_mac
        return None

    async def _get_mac_address(self, ip: str, timeout: float) -> str | None:
        """Helper to get MAC address from a device."""
        try:
            url = f"http://{ip}/rpc"
            payload = {"id": str(uuid.uuid4()), "method": "Shelly.GetDeviceInfo"}
            logger.debug("Probing MAC address for %s", ip)
            response = await self._session.post(url, json=payload, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                mac = result.get("mac")
                if not mac and "id" in result:
                    parts = result["id"].split("-")
                    if len(parts) > 1:
                        mac = parts[-1]

                if mac:
                    return self._normalize_id(mac)
            return None
        except Exception:
            return None

    def invalidate_credential_cache(self, mac: str) -> None:
        """
        Invalidate cached DigestAuth for a MAC address.

        Call this when credentials are updated to ensure the new credentials
        are used on the next request instead of the cached ones.

        Args:
            mac: Device MAC address (will be normalized)
        """
        normalized_mac = self._normalize_id(mac)
        if normalized_mac in self._digest_auth_cache:
            del self._digest_auth_cache[normalized_mac]
            logger.debug("Invalidated credential cache for MAC %s", normalized_mac)

    async def close(self) -> None:
        if not self._closed:
            await self._session.aclose()
            self._closed = True
