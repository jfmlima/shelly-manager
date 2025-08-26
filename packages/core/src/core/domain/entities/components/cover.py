from typing import Any

from pydantic import Field

from .base import Component


class CoverComponent(Component):

    state: str = Field(
        default="unknown",
        description="Cover state (open, closed, opening, closing, stopped)",
    )
    position: int | None = Field(None, description="Cover position 0-100")
    power: float = Field(default=0.0, description="Active power in watts")
    voltage: float = Field(default=0.0, description="Voltage in volts")
    current: float = Field(default=0.0, description="Current in amps")
    temperature_celsius: float | None = Field(
        None, description="Temperature in Celsius"
    )
    temperature_fahrenheit: float | None = Field(
        None, description="Temperature in Fahrenheit"
    )
    energy_total: float = Field(default=0.0, description="Total energy consumed in kWh")
    last_direction: str = Field(
        default="unknown", description="Last movement direction"
    )
    source: str = Field(default="unknown", description="Source of the cover state")

    name: str | None = Field(None, description="Cover name")
    maxtime_open: float = Field(default=60.0, description="Maximum time to open")
    maxtime_close: float = Field(default=60.0, description="Maximum time to close")
    power_limit: float = Field(default=0.0, description="Power limit in watts")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "CoverComponent":
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
            state=status.get("state", "unknown"),
            position=status.get("current_pos"),
            power=status.get("apower", 0.0),
            voltage=status.get("voltage", 0.0),
            current=status.get("current", 0.0),
            temperature_celsius=temp_c,
            temperature_fahrenheit=temp_f,
            energy_total=energy_total,
            last_direction=status.get("last_direction", "unknown"),
            source=status.get("source", "unknown"),
            name=config.get("name"),
            maxtime_open=config.get("maxtime_open", 60.0),
            maxtime_close=config.get("maxtime_close", 60.0),
            power_limit=config.get("power_limit", 0.0),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("Cover.")]
