from typing import Any, cast

import httpx

from core.domain.entities.exceptions import DeviceAuthenticationError


class LegacyHttpClient:
    """HTTP client for legacy Gen1 Shelly devices using simple HTTP GET requests."""

    def __init__(
        self,
        session: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
        connect_timeout: float = 2.0,
        max_connections: int | None = None,
    ) -> None:
        self.timeout = timeout
        self._connect_timeout = connect_timeout
        if session is not None:
            self._session = session
        else:
            pool = max_connections or 256
            self._session = httpx.AsyncClient(
                timeout=self._build_timeout(timeout),
                limits=httpx.Limits(
                    max_connections=pool,
                    max_keepalive_connections=max(1, pool // 2),
                ),
            )

    def _build_timeout(self, timeout: float | None) -> httpx.Timeout:
        """Build an httpx timeout with a short, capped connect phase."""
        effective = self.timeout if timeout is None else timeout
        return httpx.Timeout(effective, connect=min(effective, self._connect_timeout))

    async def fetch_json(
        self,
        ip: str,
        endpoint: str,
        auth: tuple[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        url = f"http://{ip}/{endpoint.lstrip('/')}"
        response = await self._session.get(
            url, timeout=self._build_timeout(timeout), auth=auth
        )
        if response.status_code == 401:
            raise DeviceAuthenticationError(ip)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(f"Endpoint {endpoint} did not return JSON object")

        return cast(dict[str, Any], data)

    async def fetch_json_optional(
        self,
        ip: str,
        endpoint: str,
        auth: tuple[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        try:
            return await self.fetch_json(ip, endpoint, auth=auth, timeout=timeout)
        except Exception:
            return {}

    async def get_with_params(
        self,
        ip: str,
        endpoint: str,
        params: dict[str, Any],
        auth: tuple[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        url = f"http://{ip}/{endpoint.lstrip('/')}"
        response = await self._session.get(
            url, params=params, timeout=self._build_timeout(timeout), auth=auth
        )
        if response.status_code == 401:
            raise DeviceAuthenticationError(ip)
        response.raise_for_status()

        try:
            data = response.json()

            if not isinstance(data, dict):
                raise ValueError(f"Endpoint {endpoint} did not return JSON object")

            return cast(dict[str, Any], data)
        except ValueError:
            # Some endpoints return non-JSON responses
            return {"response": response.text}

    async def close(self) -> None:
        await self._session.aclose()
