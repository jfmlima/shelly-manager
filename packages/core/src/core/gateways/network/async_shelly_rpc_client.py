"""
Async Shelly RPC client implementation.
"""

import time
from typing import Any

import httpx

from .network import NetworkGateway


class AsyncShellyRPCClient(NetworkGateway):

    def __init__(
        self,
        session: httpx.AsyncClient | None = None,
        timeout: int = 3,
        verify: bool | None = None,
    ):
        self.timeout = timeout
        self._session = session or httpx.AsyncClient(
            timeout=timeout, verify=True if verify is None else verify
        )
        self._closed = False

    async def make_rpc_request(
        self,
        ip: str,
        method: str,
        params: dict[str, Any] | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float = 3.0,
    ) -> tuple[dict[str, Any], float]:
        url = f"http://{ip}/rpc/{method}"

        payload = {"id": 1, "method": method}
        if params:
            payload["params"] = params

        headers = {"Content-Type": "application/json"}

        start_time = time.time()

        try:
            auth_header = None
            if auth:
                import base64

                credentials = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
                auth_header = {"Authorization": f"Basic {credentials}"}

            response = await self._session.post(
                url,
                json=payload,
                headers={**headers, **(auth_header or {})},
                timeout=timeout,
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                return response.json(), response_time
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except httpx.RequestError as e:
            response_time = time.time() - start_time
            raise Exception(f"Network error: {str(e)}") from e

    async def close(self) -> None:
        if not self._closed:
            await self._session.aclose()
            self._closed = True
