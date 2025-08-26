from typing import Any

from pydantic import Field

from .base import Component


class WebSocketComponent(Component):
    connected: bool = Field(default=False, description="WebSocket connection status")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "WebSocketComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})

        return cls(
            **base.model_dump(),
            connected=status.get("connected", False),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return []
