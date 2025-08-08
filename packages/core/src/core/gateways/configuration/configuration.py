"""
Configuration gateway interface (read-only for file config).
"""

from abc import ABC, abstractmethod
from typing import Any


class ConfigurationGateway(ABC):

    @abstractmethod
    async def get_config(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_predefined_ips(self) -> list[str]:
        pass


__all__ = ["ConfigurationGateway"]
