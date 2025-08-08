"""
Synchronous Shelly RPC client implementation.
"""

import asyncio
import time
from typing import Any

import requests

from .network import NetworkGateway


class ShellyRPCClient(NetworkGateway):

    def __init__(self, session: requests.Session | None = None, timeout: float = 1.0):
        self.session = session or requests.Session()
        self.timeout = timeout

    async def make_rpc_request(
        self,
        ip: str,
        method: str,
        params: dict | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float = 1.0,
    ) -> tuple[dict[str, Any], float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._make_sync_rpc_request, ip, method, params, auth, timeout
        )

    def _make_sync_rpc_request(
        self,
        ip: str,
        method: str,
        params: dict | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float = 1.0,
    ) -> tuple[dict[str, Any], float]:
        url = f"http://{ip}/rpc/{method}"

        payload = {"id": 1, "method": method, "params": params or {}}

        headers = {"Content-Type": "application/json"}
        start_time = time.time()

        try:
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                auth=auth,
                timeout=1,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return response.json(), response_time
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            raise Exception(f"Network error: {str(e)}") from e

    async def close(self) -> None:
        await asyncio.get_event_loop().run_in_executor(None, self.session.close)
