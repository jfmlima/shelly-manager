from typing import Any

from .components.base import Component
from .components.bluetooth_home import BluetoothHomeComponent
from .components.bluetooth_le import BluetoothLEComponent
from .components.cloud import CloudComponent
from .components.cover import CoverComponent
from .components.ethernet import EthernetComponent
from .components.input import InputComponent
from .components.knx import KnxComponent
from .components.mqtt import MqttComponent
from .components.switch import SwitchComponent
from .components.system import SystemComponent
from .components.websocket import WebSocketComponent
from .components.wifi import WifiComponent
from .components.zigbee import ZigbeeComponent


class ComponentFactory:
    @staticmethod
    def create_component(component_data: dict[str, Any]) -> Component:
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
        elif component_type == "wifi":
            return WifiComponent.from_raw_data(component_data)
        elif component_type == "ws":
            return WebSocketComponent.from_raw_data(component_data)
        elif component_type == "eth":
            return EthernetComponent.from_raw_data(component_data)
        elif component_type == "bthome":
            return BluetoothHomeComponent.from_raw_data(component_data)
        elif component_type == "ble":
            return BluetoothLEComponent.from_raw_data(component_data)
        elif component_type == "knx":
            return KnxComponent.from_raw_data(component_data)
        elif component_type == "mqtt":
            return MqttComponent.from_raw_data(component_data)
        else:
            return Component.from_raw_data(component_data)

    @staticmethod
    def create_component_from_status(
        key: str, status_data: dict[str, Any]
    ) -> Component:
        component_data = {"key": key, "status": status_data, "config": {}, "attrs": {}}
        return ComponentFactory.create_component(component_data)
