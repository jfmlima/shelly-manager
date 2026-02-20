from typing import Any

from pydantic import Field

from .base import Component


class EM1Component(Component):
    """Single-phase energy meter component (e.g., Shelly Pro EM)."""

    current: float | None = Field(None, description="Current, A")
    voltage: float | None = Field(None, description="Voltage, V")
    act_power: float | None = Field(None, description="Active power, W")
    aprt_power: float | None = Field(None, description="Apparent power, VA")
    pf: float | None = Field(None, description="Power factor")
    freq: float | None = Field(None, description="Frequency, Hz")

    name: str | None = Field(None, description="EM1 instance name")
    ct_type: str | None = Field(None, description="Current transformer type")
    reverse: bool = Field(default=False, description="Reverse CT measurement direction")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "EM1Component":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            current=status.get("current"),
            voltage=status.get("voltage"),
            act_power=status.get("act_power"),
            aprt_power=status.get("aprt_power"),
            pf=status.get("pf"),
            freq=status.get("freq"),
            name=config.get("name"),
            ct_type=config.get("ct_type"),
            reverse=config.get("reverse", False),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("EM1.")]
