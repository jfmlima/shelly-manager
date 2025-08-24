"""
Component entities for Shelly devices using Pydantic.
"""

from typing import Any

from pydantic import BaseModel, Field


class Component(BaseModel):
    """Base component entity for all Shelly device components."""

    key: str = Field(
        ..., description="Component key (e.g., 'switch:0', 'input:0', 'sys')"
    )
    component_type: str = Field(
        ..., description="Component type (e.g., 'switch', 'input', 'cover')"
    )
    component_id: int | None = Field(
        None, description="Component ID (None for system components)"
    )
    status: dict[str, Any] = Field(default_factory=dict, description="Raw status data")
    config: dict[str, Any] = Field(default_factory=dict, description="Raw config data")
    attrs: dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )
    available_actions: list[str] = Field(
        default_factory=list, description="Available actions for this component"
    )

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "Component":
        """Create component from raw JSON data."""
        key = component_data.get("key", "")
        component_type = key.split(":")[0] if ":" in key else key
        component_id = None

        # Extract component ID if present
        if ":" in key:
            try:
                component_id = int(key.split(":")[1])
            except (IndexError, ValueError):
                pass

        return cls(
            key=key,
            component_type=component_type,
            component_id=component_id,
            status=component_data.get("status", {}),
            config=component_data.get("config", {}),
            attrs=component_data.get("attrs", {}),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        """Override in subclasses to filter relevant methods.

        Args:
            all_methods: All available RPC methods from device

        Returns:
            List of action methods relevant to this component type
        """
        return [
            m
            for m in all_methods
            if m.lower().startswith(self.component_type.lower() + ".")
        ]

    def can_perform_action(self, action: str) -> bool:
        """Check if component supports specific action.

        Args:
            action: Action name to check

        Returns:
            True if action is available for this component
        """
        component_prefix = self.component_type.title()
        expected_method = f"{component_prefix}.{action}"

        return expected_method in self.available_actions


class SwitchComponent(Component):
    """Switch component with UI-friendly fields."""

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
        """Create switch component from raw JSON data."""
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
        """Filter methods relevant to switch components."""
        return [m for m in all_methods if m.startswith("Switch.")]


class InputComponent(Component):
    """Input component with UI-friendly fields."""

    state: bool = Field(default=False, description="Input state")
    input_type: str = Field(default="switch", description="Input type")
    name: str | None = Field(None, description="Input name")
    enabled: bool = Field(default=True, description="Input enabled")
    inverted: bool = Field(default=False, description="Input inverted")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "InputComponent":
        """Create input component from raw JSON data."""
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            state=status.get("state", False),
            input_type=config.get("type", "switch"),
            name=config.get("name"),
            enabled=config.get("enable", True),
            inverted=config.get("invert", False),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        """Filter methods relevant to input components."""
        return [m for m in all_methods if m.startswith("Input.")]


class CoverComponent(Component):
    """Cover/roller component with UI-friendly fields."""

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
        """Create cover component from raw JSON data."""
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
        """Filter methods relevant to cover components."""
        return [m for m in all_methods if m.startswith("Cover.")]


class SystemComponent(Component):
    """System component with device information."""

    device_name: str | None = Field(None, description="Device name")
    mac_address: str | None = Field(None, description="MAC address")
    firmware_version: str | None = Field(None, description="Firmware version")
    uptime: int = Field(default=0, description="Uptime in seconds")
    restart_required: bool = Field(default=False, description="Restart required")
    ram_total: int = Field(default=0, description="Total RAM in bytes")
    ram_free: int = Field(default=0, description="Free RAM in bytes")
    fs_total: int = Field(default=0, description="Total filesystem space in bytes")
    fs_free: int = Field(default=0, description="Free filesystem space in bytes")
    available_updates: dict[str, Any] = Field(
        default_factory=dict, description="Available updates"
    )
    unixtime: int = Field(default=0, description="Unix timestamp")
    timezone: str | None = Field(None, description="Device timezone")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "SystemComponent":
        """Create system component from raw JSON data."""
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        device_config = config.get("device", {})
        location_config = config.get("location", {})

        return cls(
            **base.model_dump(),
            device_name=device_config.get("name"),
            mac_address=status.get("mac"),
            firmware_version=device_config.get("fw_id"),
            uptime=status.get("uptime", 0),
            restart_required=status.get("restart_required", False),
            ram_total=status.get("ram_size", 0),
            ram_free=status.get("ram_free", 0),
            fs_total=status.get("fs_size", 0),
            fs_free=status.get("fs_free", 0),
            available_updates=status.get("available_updates", {}),
            unixtime=status.get("unixtime", 0),
            timezone=location_config.get("tz"),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        """Filter methods relevant to system components."""
        return [m for m in all_methods if m.startswith(("Sys.", "Shelly."))]


class CloudComponent(Component):
    """Cloud component with connectivity information."""

    connected: bool = Field(default=False, description="Cloud connection status")
    enabled: bool = Field(default=False, description="Cloud service enabled")
    server: str | None = Field(None, description="Cloud server address")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "CloudComponent":
        """Create cloud component from raw JSON data."""
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
        """Filter methods relevant to cloud components."""
        return [m for m in all_methods if m.startswith("Cloud.")]


class ZigbeeComponent(Component):
    """Zigbee component with network connectivity information."""

    network_state: str = Field(
        default="unknown", description="Zigbee network state (joined, left, etc.)"
    )
    enabled: bool = Field(default=False, description="Zigbee service enabled")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "ZigbeeComponent":
        """Create Zigbee component from raw JSON data."""
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            network_state=status.get("network_state", "unknown"),
            enabled=config.get("enable", False),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        """Filter methods relevant to Zigbee components."""
        return [
            m
            for m in all_methods
            if m.startswith("Zigbee.") or m.startswith("Shelly.Zigbee")
        ]


ComponentType = (
    Component
    | SwitchComponent
    | InputComponent
    | CoverComponent
    | SystemComponent
    | CloudComponent
    | ZigbeeComponent
)


class ComponentFactory:
    """Factory for creating appropriate component types from raw data."""

    @staticmethod
    def create_component(component_data: dict[str, Any]) -> ComponentType:
        """Create the appropriate component type from raw JSON data."""
        key = component_data.get("key", "")
        component_type = key.split(":")[0] if ":" in key else key

        if component_type == "switch":
            return SwitchComponent.from_raw_data(component_data)
        elif component_type == "input":
            return InputComponent.from_raw_data(component_data)
        elif component_type == "cover":
            return CoverComponent.from_raw_data(component_data)
        elif component_type == "sys":
            return SystemComponent.from_raw_data(component_data)
        elif component_type == "cloud":
            return CloudComponent.from_raw_data(component_data)
        elif component_type == "zigbee":
            return ZigbeeComponent.from_raw_data(component_data)
        else:
            return Component.from_raw_data(component_data)
