"""
Device gateway interface.
"""

from abc import ABC, abstractmethod
from typing import Any

from ...domain.entities.device_status import DeviceStatus
from ...domain.entities.discovered_device import DiscoveredDevice
from ...domain.value_objects.action_result import ActionResult


class DeviceGateway(ABC):
    timeout: float = 10.0

    @abstractmethod
    async def discover_device(self, ip: str) -> DiscoveredDevice | None:
        pass

    @abstractmethod
    async def get_device_status(self, ip: str) -> DeviceStatus | None:
        """Get device components and status information."""
        pass

    @abstractmethod
    async def get_available_methods(self, ip: str) -> list[str]:
        """Get available RPC methods for action validation."""
        pass

    @abstractmethod
    async def execute_component_action(
        self,
        ip: str,
        component_key: str,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> ActionResult:
        """Execute validated action on any component type."""
        pass

    @abstractmethod
    async def execute_bulk_action(
        self,
        device_ips: list[str],
        component_key: str,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[ActionResult]:
        """Execute component actions on multiple devices in parallel."""
        pass
