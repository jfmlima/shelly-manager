from typing import Any

from pydantic import Field

from .base import Component


class EMDataComponent(Component):
    """3-phase accumulated energy data component (e.g., Shelly Pro 3EM)."""

    a_total_act_energy: float = Field(
        default=0.0, description="Phase A total active energy, Wh"
    )
    a_total_act_ret_energy: float = Field(
        default=0.0, description="Phase A total active returned energy, Wh"
    )
    b_total_act_energy: float = Field(
        default=0.0, description="Phase B total active energy, Wh"
    )
    b_total_act_ret_energy: float = Field(
        default=0.0, description="Phase B total active returned energy, Wh"
    )
    c_total_act_energy: float = Field(
        default=0.0, description="Phase C total active energy, Wh"
    )
    c_total_act_ret_energy: float = Field(
        default=0.0, description="Phase C total active returned energy, Wh"
    )
    total_act: float = Field(
        default=0.0, description="Total active energy on all phases, Wh"
    )
    total_act_ret: float = Field(
        default=0.0, description="Total active returned energy on all phases, Wh"
    )

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "EMDataComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})

        return cls(
            **base.model_dump(),
            a_total_act_energy=status.get("a_total_act_energy", 0.0),
            a_total_act_ret_energy=status.get("a_total_act_ret_energy", 0.0),
            b_total_act_energy=status.get("b_total_act_energy", 0.0),
            b_total_act_ret_energy=status.get("b_total_act_ret_energy", 0.0),
            c_total_act_energy=status.get("c_total_act_energy", 0.0),
            c_total_act_ret_energy=status.get("c_total_act_ret_energy", 0.0),
            total_act=status.get("total_act", 0.0),
            total_act_ret=status.get("total_act_ret", 0.0),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("EMData.")]
