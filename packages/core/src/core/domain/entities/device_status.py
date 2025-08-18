"""
Device components entity to hold component data.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .components import (
    CloudComponent,
    ComponentFactory,
    ComponentType,
    CoverComponent,
    InputComponent,
    SwitchComponent,
    SystemComponent,
    ZigbeeComponent,
)


class DeviceStatus(BaseModel):
    """Entity containing all components of a Shelly device."""

    device_ip: str = Field(..., description="Device IP address")
    components: list[ComponentType] = Field(
        default_factory=list, description="List of device components"
    )
    cfg_rev: int = Field(default=0, description="Configuration revision")
    total_components: int = Field(default=0, description="Total number of components")
    offset: int = Field(default=0, description="Component offset in response")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    @classmethod
    def from_raw_response(
        cls, device_ip: str, response_data: dict[str, Any], zigbee_data: dict[str, Any] | None = None
    ) -> "DeviceStatus":
        """Create DeviceStatus from raw shelly.getcomponents response and optional Zigbee data."""
        components_data = response_data.get("components", [])
        components = []

        for component_data in components_data:
            component = ComponentFactory.create_component(component_data)
            components.append(component)

        if zigbee_data:
            zigbee_component_data = {
                "key": "zigbee",
                "status": zigbee_data,
                "config": {},
                "attrs": {}
            }
            zigbee_component = ZigbeeComponent.from_raw_data(zigbee_component_data)
            components.append(zigbee_component)

        return cls(
            device_ip=device_ip,
            components=components,
            cfg_rev=response_data.get("cfg_rev", 0),
            total_components=response_data.get("total", len(components)),
            offset=response_data.get("offset", 0),
            last_updated=datetime.now(),
        )

    def get_switches(self) -> list[SwitchComponent]:
        """Get all switch components."""
        return [comp for comp in self.components if isinstance(comp, SwitchComponent)]

    def get_inputs(self) -> list[InputComponent]:
        """Get all input components."""
        return [comp for comp in self.components if isinstance(comp, InputComponent)]

    def get_covers(self) -> list[CoverComponent]:
        """Get all cover components."""
        return [comp for comp in self.components if isinstance(comp, CoverComponent)]

    def get_system_info(self) -> SystemComponent | None:
        """Get system component (device information)."""
        for comp in self.components:
            if isinstance(comp, SystemComponent):
                return comp
        return None

    def get_cloud_info(self) -> CloudComponent | None:
        """Get cloud component (connectivity information)."""
        for comp in self.components:
            if isinstance(comp, CloudComponent):
                return comp
        return None

    def get_zigbee_info(self) -> ZigbeeComponent | None:
        """Get zigbee component (network connectivity information)."""
        for comp in self.components:
            if isinstance(comp, ZigbeeComponent):
                return comp
        return None

    def get_component_by_key(self, key: str) -> ComponentType | None:
        """Get component by its key."""
        for comp in self.components:
            if comp.key == key:
                return comp
        return None

    def get_components_by_type(self, component_type: str) -> list[ComponentType]:
        """Get all components of a specific type."""
        return [
            comp for comp in self.components if comp.component_type == component_type
        ]

    def has_component_type(self, component_type: str) -> bool:
        """Check if device has components of a specific type."""
        return any(comp.component_type == component_type for comp in self.components)

    def get_device_summary(self) -> dict[str, Any]:
        """Get a summary of device capabilities for UI."""
        sys_info = self.get_system_info()
        cloud_info = self.get_cloud_info()
        zigbee_info = self.get_zigbee_info()

        has_updates = False
        update_info = {}
        if sys_info and sys_info.available_updates:
            for update_type, update_data in sys_info.available_updates.items():
                if isinstance(update_data, dict) and update_data.get("version"):
                    has_updates = True
                    update_info[update_type] = {
                        "version": update_data.get("version"),
                        "build_id": update_data.get("build_id"),
                        "name": update_data.get("name"),
                        "description": update_data.get("desc"),
                    }

        return {
            "device_name": sys_info.device_name if sys_info else None,
            "mac_address": sys_info.mac_address if sys_info else None,
            "firmware_version": sys_info.firmware_version if sys_info else None,
            "uptime": sys_info.uptime if sys_info else 0,
            "cloud_connected": cloud_info.connected if cloud_info else False,
            "zigbee_connected": zigbee_info.network_state == "joined" if zigbee_info else False,
            "switch_count": len(self.get_switches()),
            "input_count": len(self.get_inputs()),
            "cover_count": len(self.get_covers()),
            "total_power": sum(switch.power for switch in self.get_switches()),
            "any_switch_on": any(switch.output for switch in self.get_switches()),
            "has_updates": has_updates,
            "available_updates": update_info,
            "restart_required": sys_info.restart_required if sys_info else False,
            "last_updated": self.last_updated.isoformat(),
        }
