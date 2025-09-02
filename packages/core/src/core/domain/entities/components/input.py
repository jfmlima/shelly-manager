from typing import Any

from pydantic import Field

from .base import Component


class InputComponent(Component):
    state: bool = Field(default=False, description="Input state")
    input_type: str = Field(default="switch", description="Input type")
    name: str | None = Field(None, description="Input name")
    enabled: bool = Field(default=True, description="Input enabled")
    inverted: bool = Field(default=False, description="Input inverted")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "InputComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            state=status.get("state", False) or False,
            input_type=config.get("type", "switch") or "switch",
            name=config.get("name"),
            enabled=config.get("enable", False) or False,
            inverted=config.get("invert", False) or False,
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("Input.")]
