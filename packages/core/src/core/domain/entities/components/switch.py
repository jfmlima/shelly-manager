from typing import Any

from pydantic import Field

from .base import Component


class SwitchComponent(Component):
    output: bool = Field(default=False, description="Switch output state")
    power: float = Field(default=0.0, description="Active power in watts")
    voltage: float = Field(default=0.0, description="Voltage in volts")
    current: float = Field(default=0.0, description="Current in amps")
    frequency: float = Field(default=0.0, description="Frequency in Hz")
    temperature_celsius: float | None = Field(
        None, description="Temperature in Celsius"
    )
    temperature_fahrenheit: float | None = Field(
        None, description="Temperature in Fahrenheit"
    )
    energy_total: float = Field(default=0.0, description="Total energy consumed in kWh")
    power_factor: float = Field(default=0.0, description="Power factor")
    source: str = Field(default="unknown", description="Source of the switch state")

    name: str | None = Field(None, description="Switch name")
    auto_on: bool = Field(default=False, description="Auto-on enabled")
    auto_off: bool = Field(default=False, description="Auto-off enabled")
    power_limit: float = Field(default=0.0, description="Power limit in watts")
    current_limit: float = Field(default=0.0, description="Current limit in amps")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "SwitchComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        temp_data = status.get("temperature", {})
        temp_c = temp_data.get("tC") if isinstance(temp_data, dict) else None
        temp_f = temp_data.get("tF") if isinstance(temp_data, dict) else None

        energy_data = status.get("aenergy", {})
        energy_total = (
            energy_data.get("total", 0.0) if isinstance(energy_data, dict) else 0.0
        )

        return cls(
            **base.model_dump(),
            output=status.get("output", False),
            power=status.get("apower", 0.0),
            voltage=status.get("voltage", 0.0),
            current=status.get("current", 0.0),
            frequency=status.get("freq", 0.0),
            temperature_celsius=temp_c,
            temperature_fahrenheit=temp_f,
            energy_total=energy_total,
            power_factor=status.get("pf", 0.0),
            source=status.get("source", "unknown"),
            name=config.get("name"),
            auto_on=config.get("auto_on", False),
            auto_off=config.get("auto_off", False),
            power_limit=config.get("power_limit", 0.0),
            current_limit=config.get("current_limit", 0.0),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("Switch.")]
