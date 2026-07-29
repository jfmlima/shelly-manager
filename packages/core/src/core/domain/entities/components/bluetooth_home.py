from typing import Any

from pydantic import Field

from .base import Component


class BluetoothHomeComponent(Component):
    errors: list[str] = Field(default_factory=list, description="Bluetooth Home errors")
    enabled: bool = Field(default=False, description="Bluetooth Home enabled")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "BluetoothHomeComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            errors=status.get("errors", []),
            enabled=config.get("enable", False),
        )
