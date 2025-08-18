"""
Device gateway interface.
"""

from abc import ABC, abstractmethod
from typing import Any

from ...domain.entities.device_status import DeviceStatus
from ...domain.entities.discovered_device import DiscoveredDevice
from ...domain.value_objects.action_result import ActionResult


class DeviceGateway(ABC):
    timeout: float = 3.0

    @abstractmethod
    async def discover_device(self, ip: str) -> DiscoveredDevice | None:
        pass

    @abstractmethod
    async def get_device_status(self, ip: str) -> DeviceStatus | None:
        """Get device components and status information."""
        pass

    @abstractmethod
    async def execute_action(
        self, ip: str, action_type: str, parameters: dict[str, Any]
    ) -> ActionResult:
        pass

    @abstractmethod
    async def get_device_config(self, ip: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def set_device_config(self, ip: str, config: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    async def execute_bulk_action(
        self, device_ips: list[str], action_type: str, parameters: dict[str, Any]
    ) -> list[ActionResult]:
        pass
