from typing import Any

from pydantic import Field

from .base import Component


class CloudComponent(Component):
    connected: bool = Field(default=False, description="Cloud connection status")
    enabled: bool = Field(default=False, description="Cloud service enabled")
    server: str | None = Field(None, description="Cloud server address")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "CloudComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            connected=status.get("connected", False),
            enabled=config.get("enable", False),
            server=config.get("server"),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("Cloud.")]
