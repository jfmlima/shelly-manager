from typing import get_args

import pytest
from core.domain.entities.components import (
    BluetoothHomeComponent,
    BluetoothLEComponent,
    CloudComponent,
    Component,
    ComponentFactory,
    ComponentType,
    CoverComponent,
    EM1Component,
    EM1DataComponent,
    EMComponent,
    EMDataComponent,
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
from core.domain.entities.components.registry import COMPONENT_MODELS, model_for
from core.domain.value_objects.component_namespace import known_component_types

# Spelled out rather than derived from the registry: a test that walks the table
# it is checking passes just as happily when an entry is dropped or points at
# the wrong model.
EXPECTED_MODELS = {
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


class TestComponentRegistry:
    def test_it_maps_every_type_to_its_own_model(self):
        assert COMPONENT_MODELS == EXPECTED_MODELS

    def test_it_dispatches_to_every_model_the_union_declares(self):
        declared = set(get_args(ComponentType)) - {Component}

        assert set(COMPONENT_MODELS.values()) == declared

    def test_it_registers_only_known_component_types(self):
        assert set(COMPONENT_MODELS) <= known_component_types()

    def test_it_falls_back_to_the_base_model_for_an_unregistered_type(self):
        assert model_for("light") is Component
        assert model_for("nonsense") is Component


class TestRegisteredModelsParseTheirOwnFields:
    """The types the rest of the suite never builds through the factory.

    ``isinstance`` is what proves the mapping, since every model subclasses
    ``Component`` directly and a wrong entry fails it. Reading a field then
    shows the model parsed its own payload rather than merely being built.
    Six of the seven fields are unique to their model; ``connected`` is not,
    so the cloud case rests on ``isinstance`` alone.
    """

    @pytest.mark.parametrize(
        "raw,expected_model,field,value",
        [
            (
                {"key": "cover:0", "status": {"state": "open", "current_pos": 70}},
                CoverComponent,
                "position",
                70,
            ),
            (
                {"key": "cloud", "status": {"connected": True}},
                CloudComponent,
                "connected",
                True,
            ),
            (
                {"key": "eth", "status": {"ip": "10.0.0.4"}},
                EthernetComponent,
                "eth_ip",
                "10.0.0.4",
            ),
            (
                {"key": "bthome", "status": {"errors": ["no_bt"]}},
                BluetoothHomeComponent,
                "errors",
                ["no_bt"],
            ),
            (
                {"key": "ble", "config": {"rpc": {"enable": True}}},
                BluetoothLEComponent,
                "rpc_enabled",
                True,
            ),
            (
                {"key": "knx", "config": {"ia": "1.1.5"}},
                KnxComponent,
                "individual_address",
                "1.1.5",
            ),
            (
                {"key": "mqtt", "config": {"client_id": "shelly-1"}},
                MqttComponent,
                "client_id",
                "shelly-1",
            ),
        ],
    )
    def test_it_parses_a_type_specific_field(self, raw, expected_model, field, value):
        component = ComponentFactory.create_component(raw)

        assert isinstance(component, expected_model)
        assert getattr(component, field) == value
