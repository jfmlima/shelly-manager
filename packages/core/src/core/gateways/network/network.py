"""
Network gateway interface.
"""

from abc import ABC, abstractmethod
from typing import Any


class NetworkGateway(ABC):

    @abstractmethod
    async def make_rpc_request(
        self,
        ip: str,
        method: str,
        params: dict[str, Any] | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float = 3.0,
    ) -> tuple[dict[str, Any], float]:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
