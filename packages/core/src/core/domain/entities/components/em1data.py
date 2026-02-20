from typing import Any

from pydantic import Field

from .base import Component


class EM1DataComponent(Component):
    """Single-phase accumulated energy data component (e.g., Shelly Pro EM)."""

    total_act_energy: float = Field(default=0.0, description="Total active energy, Wh")
    total_act_ret_energy: float = Field(
        default=0.0, description="Total active returned energy, Wh"
    )

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "EM1DataComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})

        return cls(
            **base.model_dump(),
            total_act_energy=status.get("total_act_energy", 0.0),
            total_act_ret_energy=status.get("total_act_ret_energy", 0.0),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("EM1Data.")]
