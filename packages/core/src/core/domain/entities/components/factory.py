from typing import Any

from .base import Component
from .bluetooth_home import BluetoothHomeComponent
from .bluetooth_le import BluetoothLEComponent
from .cloud import CloudComponent
from .cover import CoverComponent
from .em import EMComponent
from .em1 import EM1Component
from .em1data import EM1DataComponent
from .emdata import EMDataComponent
from .ethernet import EthernetComponent
from .input import InputComponent
from .knx import KnxComponent
from .mqtt import MqttComponent
from .switch import SwitchComponent
from .system import SystemComponent
from .websocket import WebSocketComponent
from .wifi import WifiComponent
from .zigbee import ZigbeeComponent


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
        elif component_type == "em":
            return EMComponent.from_raw_data(component_data)
        elif component_type == "em1":
            return EM1Component.from_raw_data(component_data)
        elif component_type == "emdata":
            return EMDataComponent.from_raw_data(component_data)
        elif component_type == "em1data":
            return EM1DataComponent.from_raw_data(component_data)
        else:
            return Component.from_raw_data(component_data)

    @staticmethod
    def create_component_from_status(
        key: str, status_data: dict[str, Any]
    ) -> Component:
        component_data = {"key": key, "status": status_data, "config": {}, "attrs": {}}
        return ComponentFactory.create_component(component_data)
