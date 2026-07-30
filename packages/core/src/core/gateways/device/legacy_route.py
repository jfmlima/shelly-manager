"""The way to a Gen1 device, whether or not there is one.

``ShellyDeviceGateway`` speaks RPC to Gen2+ devices and the legacy HTTP API to
Gen1 ones, and is also built with no legacy gateway at all. This is the single
seam between the two paths: with no legacy gateway behind it, it answers
"nothing here" rather than asking every caller to check first.
"""

from typing import Any

from ...domain.entities.device_status import DeviceStatus
from ...domain.entities.discovered_device import DiscoveredDevice
from ...domain.value_objects.action_envelope import ActionEnvelope
from ...domain.value_objects.action_result import ActionResult
from .legacy_device_gateway import LegacyDeviceGateway


class LegacyRoute:

    def __init__(self, gateway: LegacyDeviceGateway | None) -> None:
        self._gateway = gateway

    async def discover_device(self, ip: str, timeout: float) -> DiscoveredDevice | None:
        if self._gateway is None:
            return None
        return await self._gateway.discover_device(ip, timeout=timeout)

    async def get_device_status(self, ip: str) -> DeviceStatus | None:
        if self._gateway is None:
            return None
        return await self._gateway.get_device_status(ip)

    async def get_settings(self, ip: str) -> dict[str, Any] | None:
        if self._gateway is None:
            return None
        return await self._gateway.fetch_settings(ip)

    async def execute_action(
        self,
        ip: str,
        component_key: str,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> ActionResult:
        """Run a ``Legacy.`` action, or report that there is nowhere to run it.

        The action name stays as written, so the refusal carries the same
        action type the legacy gateway would have reported for it.
        """
        if self._gateway is None:
            envelope = ActionEnvelope(
                device_ip=ip, action_type=f"{component_key}.{action}"
            )
            return envelope.failed(
                message="Legacy gateway not available",
                error="Legacy operations require legacy gateway injection",
            )
        return await self._gateway.execute_action(
            ip, component_key, action, parameters or {}
        )

    def invalidate_credentials(self, mac: str) -> None:
        if self._gateway is not None:
            self._gateway.invalidate_credential_cache(mac)
