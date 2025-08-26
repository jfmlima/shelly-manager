from typing import Any

from pydantic import Field

from .base import Component


class SystemComponent(Component):
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
        return [m for m in all_methods if m.startswith(("Sys.", "Shelly."))]
