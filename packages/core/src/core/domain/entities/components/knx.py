from typing import Any

from pydantic import Field

from .base import Component


class KnxComponent(Component):
    enabled: bool = Field(default=False, description="KNX service enabled")
    individual_address: str | None = Field(None, description="KNX individual address")
    routing_address: str | None = Field(None, description="KNX routing address")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "KnxComponent":
        base = Component.from_raw_data(component_data)
        config = component_data.get("config", {})

        routing_config = config.get("routing", {})

        return cls(
            **base.model_dump(),
            enabled=config.get("enable", False),
            individual_address=config.get("ia"),
            routing_address=routing_config.get("addr"),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("KNX.")]
