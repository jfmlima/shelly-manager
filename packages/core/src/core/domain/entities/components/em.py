from typing import Any

from pydantic import Field

from .base import Component


class EMComponent(Component):
    """3-phase energy meter component (e.g., Shelly Pro 3EM)."""

    a_current: float | None = Field(None, description="Phase A current, A")
    a_voltage: float | None = Field(None, description="Phase A voltage, V")
    a_act_power: float | None = Field(None, description="Phase A active power, W")
    a_aprt_power: float | None = Field(None, description="Phase A apparent power, VA")
    a_pf: float | None = Field(None, description="Phase A power factor")
    a_freq: float | None = Field(None, description="Phase A frequency, Hz")

    b_current: float | None = Field(None, description="Phase B current, A")
    b_voltage: float | None = Field(None, description="Phase B voltage, V")
    b_act_power: float | None = Field(None, description="Phase B active power, W")
    b_aprt_power: float | None = Field(None, description="Phase B apparent power, VA")
    b_pf: float | None = Field(None, description="Phase B power factor")
    b_freq: float | None = Field(None, description="Phase B frequency, Hz")

    c_current: float | None = Field(None, description="Phase C current, A")
    c_voltage: float | None = Field(None, description="Phase C voltage, V")
    c_act_power: float | None = Field(None, description="Phase C active power, W")
    c_aprt_power: float | None = Field(None, description="Phase C apparent power, VA")
    c_pf: float | None = Field(None, description="Phase C power factor")
    c_freq: float | None = Field(None, description="Phase C frequency, Hz")

    n_current: float | None = Field(None, description="Neutral current, A")

    total_current: float | None = Field(None, description="Total current, A")
    total_act_power: float | None = Field(None, description="Total active power, W")
    total_aprt_power: float | None = Field(None, description="Total apparent power, VA")

    name: str | None = Field(None, description="EM instance name")
    ct_type: str | None = Field(None, description="Current transformer type")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "EMComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            a_current=status.get("a_current"),
            a_voltage=status.get("a_voltage"),
            a_act_power=status.get("a_act_power"),
            a_aprt_power=status.get("a_aprt_power"),
            a_pf=status.get("a_pf"),
            a_freq=status.get("a_freq"),
            b_current=status.get("b_current"),
            b_voltage=status.get("b_voltage"),
            b_act_power=status.get("b_act_power"),
            b_aprt_power=status.get("b_aprt_power"),
            b_pf=status.get("b_pf"),
            b_freq=status.get("b_freq"),
            c_current=status.get("c_current"),
            c_voltage=status.get("c_voltage"),
            c_act_power=status.get("c_act_power"),
            c_aprt_power=status.get("c_aprt_power"),
            c_pf=status.get("c_pf"),
            c_freq=status.get("c_freq"),
            n_current=status.get("n_current"),
            total_current=status.get("total_current"),
            total_act_power=status.get("total_act_power"),
            total_aprt_power=status.get("total_aprt_power"),
            name=config.get("name"),
            ct_type=config.get("ct_type"),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("EM.")]
