"""Which model class parses which component type.

The key set is a subset of the namespace table's, held there by
``test_it_registers_only_known_component_types``. That table is the list of
type keys Shelly actually uses, so a key only this one knows is either a
misspelling no device will ever match or a new type the namespace table has to
learn as well. Its fallback for an unknown type guesses one title-cased
namespace, which matches case-insensitively and so usually discovers the same
methods, but it loses the second namespace ``sys`` answers to and the exact
method ``zigbee`` owns outside its own.
"""

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

COMPONENT_MODELS: dict[str, type[Component]] = {
    "ble": BluetoothLEComponent,
    "bthome": BluetoothHomeComponent,
    "cloud": CloudComponent,
    "cover": CoverComponent,
    "em": EMComponent,
    "em1": EM1Component,
    "em1data": EM1DataComponent,
    "emdata": EMDataComponent,
    "eth": EthernetComponent,
    "input": InputComponent,
    "knx": KnxComponent,
    "mqtt": MqttComponent,
    "switch": SwitchComponent,
    "sys": SystemComponent,
    "wifi": WifiComponent,
    "ws": WebSocketComponent,
    "zigbee": ZigbeeComponent,
}


def model_for(component_type: str) -> type[Component]:
    """The model class parsing a component type, or the untyped base."""
    return COMPONENT_MODELS.get(component_type, Component)
