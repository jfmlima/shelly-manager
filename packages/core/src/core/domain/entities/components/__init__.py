from .base import Component
from .bluetooth_home import BluetoothHomeComponent
from .bluetooth_le import BluetoothLEComponent
from .cloud import CloudComponent
from .cover import CoverComponent
from .ethernet import EthernetComponent
from .factory import ComponentFactory
from .input import InputComponent
from .knx import KnxComponent
from .mqtt import MqttComponent
from .switch import SwitchComponent
from .system import SystemComponent
from .websocket import WebSocketComponent
from .wifi import WifiComponent
from .zigbee import ZigbeeComponent

ComponentType = (
    Component
    | SwitchComponent
    | InputComponent
    | CoverComponent
    | SystemComponent
    | CloudComponent
    | ZigbeeComponent
    | WifiComponent
    | WebSocketComponent
    | EthernetComponent
    | BluetoothHomeComponent
    | BluetoothLEComponent
    | KnxComponent
    | MqttComponent
)

__all__ = [
    "Component",
    "ComponentType",
    "ComponentFactory",
    "SwitchComponent",
    "InputComponent",
    "CoverComponent",
    "SystemComponent",
    "CloudComponent",
    "ZigbeeComponent",
    "WifiComponent",
    "WebSocketComponent",
    "EthernetComponent",
    "BluetoothHomeComponent",
    "BluetoothLEComponent",
    "KnxComponent",
    "MqttComponent",
]
