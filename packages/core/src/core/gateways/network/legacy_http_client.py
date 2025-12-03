import asyncio
from typing import Any, cast

import requests


class LegacyHttpClient:
    """HTTP client for legacy Gen1 Shelly devices using simple HTTP GET requests."""

    def __init__(
        self, session: requests.Session | None = None, timeout: float = 10.0
    ) -> None:
        self.timeout = timeout
        self._session = session or requests.Session()

    async def fetch_json(self, ip: str, endpoint: str) -> dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_fetch_json, ip, endpoint)

    async def fetch_json_optional(self, ip: str, endpoint: str) -> dict[str, Any]:
        try:
            return await self.fetch_json(ip, endpoint)
        except Exception:
            return {}

    async def get_with_params(
        self, ip: str, endpoint: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(
            None, self._sync_get_with_params, ip, endpoint, params
        )

    def _sync_fetch_json(self, ip: str, endpoint: str) -> dict[str, Any]:
        url = f"http://{ip}/{endpoint.lstrip('/')}"
        response = self._session.get(url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(f"Endpoint {endpoint} did not return JSON object")

        return cast(dict[str, Any], data)

    def _sync_get_with_params(
        self, ip: str, endpoint: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"http://{ip}/{endpoint.lstrip('/')}"
        response = self._session.get(url, params=params, timeout=self.timeout)
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
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._session.close)
