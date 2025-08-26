from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .components import (
    BluetoothHomeComponent,
    BluetoothLEComponent,
    CloudComponent,
    ComponentType,
    CoverComponent,
    EthernetComponent,
    InputComponent,
    KnxComponent,
    MqttComponent,
    SwitchComponent,
    SystemComponent,
    WebSocketComponent,
    WifiComponent,
    ZigbeeComponent,
)
from .factory import ComponentFactory


class DeviceStatus(BaseModel):
    device_ip: str = Field(..., description="Device IP address")
    components: list[ComponentType] = Field(
        default_factory=list, description="List of device components"
    )
    cfg_rev: int = Field(default=0, description="Configuration revision")
    total_components: int = Field(default=0, description="Total number of components")
    offset: int = Field(default=0, description="Component offset in response")
    available_methods: list[str] = Field(
        default_factory=list, description="Available RPC methods"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    device_name: str | None = Field(None, description="Device name from device info")
    device_type: str | None = Field(
        None, description="Device type/model from device info"
    )
    firmware_version: str | None = Field(
        None, description="Firmware version from device info"
    )
    mac_address: str | None = Field(None, description="MAC address from device info")
    app_name: str | None = Field(None, description="App name from device info")

    @classmethod
    def from_raw_response(
        cls,
        device_ip: str,
        response_data: dict[str, Any],
        available_methods: list[str] | None = None,
        device_info_data: dict[str, Any] | None = None,
        status_data: dict[str, Any] | None = None,
    ) -> "DeviceStatus":
        components_data = response_data.get("components", [])
        components = []
        methods = available_methods or []
        status_dict = status_data or {}

        component_keys = {comp["key"] for comp in components_data}
        for component_data in components_data:
            component = ComponentFactory.create_component(component_data)
            component.available_actions = component.get_available_actions(methods)
            components.append(component)

        for key, status in status_dict.items():
            if key not in component_keys and isinstance(status, dict):
                component = ComponentFactory.create_component_from_status(key, status)
                component.available_actions = component.get_available_actions(methods)
                components.append(component)

        device_info = device_info_data or {}

        return cls(
            device_ip=device_ip,
            components=components,
            cfg_rev=response_data.get("cfg_rev", 0),
            total_components=response_data.get("total", len(components)),
            offset=response_data.get("offset", 0),
            available_methods=methods,
            last_updated=datetime.now(),
            device_name=device_info.get("name"),
            device_type=device_info.get("model"),
            firmware_version=device_info.get("fw_id"),
            mac_address=device_info.get("mac"),
            app_name=device_info.get("app"),
        )

    def get_switches(self) -> list[SwitchComponent]:
        return [comp for comp in self.components if isinstance(comp, SwitchComponent)]

    def get_inputs(self) -> list[InputComponent]:
        return [comp for comp in self.components if isinstance(comp, InputComponent)]

    def get_covers(self) -> list[CoverComponent]:
        return [comp for comp in self.components if isinstance(comp, CoverComponent)]

    def get_system_info(self) -> SystemComponent | None:
        for comp in self.components:
            if isinstance(comp, SystemComponent):
                return comp
        return None

    def get_cloud_info(self) -> CloudComponent | None:
        for comp in self.components:
            if isinstance(comp, CloudComponent):
                return comp
        return None

    def get_zigbee_info(self) -> ZigbeeComponent | None:
        for comp in self.components:
            if isinstance(comp, ZigbeeComponent):
                return comp
        return None

    def get_wifi_info(self) -> WifiComponent | None:
        for comp in self.components:
            if isinstance(comp, WifiComponent):
                return comp
        return None

    def get_websocket_info(self) -> WebSocketComponent | None:
        for comp in self.components:
            if isinstance(comp, WebSocketComponent):
                return comp
        return None

    def get_ethernet_info(self) -> EthernetComponent | None:
        for comp in self.components:
            if isinstance(comp, EthernetComponent):
                return comp
        return None

    def get_bluetooth_home_info(self) -> BluetoothHomeComponent | None:
        for comp in self.components:
            if isinstance(comp, BluetoothHomeComponent):
                return comp
        return None

    def get_bluetooth_le_info(self) -> BluetoothLEComponent | None:
        for comp in self.components:
            if isinstance(comp, BluetoothLEComponent):
                return comp
        return None

    def get_knx_info(self) -> KnxComponent | None:
        for comp in self.components:
            if isinstance(comp, KnxComponent):
                return comp
        return None

    def get_mqtt_info(self) -> MqttComponent | None:
        for comp in self.components:
            if isinstance(comp, MqttComponent):
                return comp
        return None

    def get_component_by_key(self, key: str) -> ComponentType | None:
        for comp in self.components:
            if comp.key == key:
                return comp
        return None

    def get_components_by_type(self, component_type: str) -> list[ComponentType]:
        return [
            comp for comp in self.components if comp.component_type == component_type
        ]

    def has_component_type(self, component_type: str) -> bool:
        return any(comp.component_type == component_type for comp in self.components)

    def get_device_summary(self) -> dict[str, Any]:
        sys_info = self.get_system_info()
        cloud_info = self.get_cloud_info()
        zigbee_info = self.get_zigbee_info()
        wifi_info = self.get_wifi_info()
        websocket_info = self.get_websocket_info()

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
            "device_name": self.device_name
            or (sys_info.device_name if sys_info else None),
            "mac_address": self.mac_address
            or (sys_info.mac_address if sys_info else None),
            "firmware_version": self.firmware_version
            or (sys_info.firmware_version if sys_info else None),
            "uptime": sys_info.uptime if sys_info else 0,
            "cloud_connected": cloud_info.connected if cloud_info else False,
            "zigbee_connected": (
                zigbee_info.network_state == "joined" if zigbee_info else False
            ),
            "zigbee_network_state": zigbee_info.network_state if zigbee_info else None,
            "wifi_connected": wifi_info.wifi_status == "got ip" if wifi_info else False,
            "wifi_ssid": wifi_info.ssid if wifi_info else None,
            "wifi_ip": wifi_info.sta_ip if wifi_info else None,
            "wifi_rssi": wifi_info.rssi if wifi_info else None,
            "websocket_connected": (
                websocket_info.connected if websocket_info else False
            ),
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
