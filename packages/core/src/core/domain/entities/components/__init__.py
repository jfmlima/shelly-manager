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
    | EMComponent
    | EM1Component
    | EMDataComponent
    | EM1DataComponent
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
    "EMComponent",
    "EM1Component",
    "EMDataComponent",
    "EM1DataComponent",
]
