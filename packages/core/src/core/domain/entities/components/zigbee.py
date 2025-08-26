from typing import Any

from pydantic import Field

from .base import Component


class ZigbeeComponent(Component):

    network_state: str = Field(
        default="unknown", description="Zigbee network state (joined, left, etc.)"
    )
    enabled: bool = Field(default=False, description="Zigbee service enabled")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "ZigbeeComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            network_state=status.get("network_state", "unknown"),
            enabled=config.get("enable", False),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [
            m
            for m in all_methods
            if m.startswith("Zigbee.") or m.startswith("Shelly.Zigbee")
        ]
