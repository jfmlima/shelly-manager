import pytest
from core.domain.entities.components import (
    Component,
    InputComponent,
    SwitchComponent,
    WebSocketComponent,
    WifiComponent,
    ZigbeeComponent,
)
from core.domain.entities.factory import ComponentFactory


class TestZigbeeComponent:

    def test_it_creates_zigbee_component_from_raw_data(self):
        raw_data = {
            "key": "zigbee",
            "status": {"network_state": "joined"},
            "config": {"enable": True},
            "attrs": {},
        }

        component = ZigbeeComponent.from_raw_data(raw_data)

        assert component.key == "zigbee"
        assert component.component_type == "zigbee"
        assert component.network_state == "joined"
        assert component.enabled is True
        assert component.status == {"network_state": "joined"}
        assert component.config == {"enable": True}

    def test_it_creates_zigbee_component_with_defaults(self):
        raw_data = {"key": "zigbee", "status": {}, "config": {}, "attrs": {}}

        component = ZigbeeComponent.from_raw_data(raw_data)

        assert component.network_state == "unknown"
        assert component.enabled is False

    def test_it_creates_zigbee_component_with_network_state(self):
        raw_data = {
            "key": "zigbee",
            "status": {"network_state": "left"},
            "config": {"enable": False},
            "attrs": {},
        }

        component = ZigbeeComponent.from_raw_data(raw_data)

        assert component.network_state == "left"
        assert component.enabled is False


class TestComponentFactory:
    def test_it_creates_zigbee_component_for_zigbee_type(self):
        raw_data = {
            "key": "zigbee",
            "status": {"network_state": "joined"},
            "config": {"enable": True},
            "attrs": {},
        }

        component = ComponentFactory.create_component(raw_data)

        assert isinstance(component, ZigbeeComponent)
        assert component.network_state == "joined"
        assert component.enabled is True

    def test_it_creates_switch_component_for_switch_type(self):
        raw_data = {
            "key": "switch:0",
            "status": {"output": True},
            "config": {"name": "Test Switch"},
            "attrs": {},
        }

        component = ComponentFactory.create_component(raw_data)

        assert isinstance(component, SwitchComponent)
        assert component.output is True
        assert component.name == "Test Switch"

    def test_it_creates_base_component_for_unknown_type(self):
        raw_data = {
            "key": "unknown:component",
            "status": {"some_field": "value"},
            "config": {},
            "attrs": {},
        }

        component = ComponentFactory.create_component(raw_data)

        assert isinstance(component, Component)
        assert component.key == "unknown:component"
        assert component.component_type == "unknown"


class TestComponentIntegration:
    def test_it_verifies_zigbee_component_inheritance(self):
        component = ZigbeeComponent(
            key="zigbee", component_type="zigbee", network_state="joined", enabled=True
        )

        assert isinstance(component, Component)
        assert isinstance(component, ZigbeeComponent)
        assert component.key == "zigbee"
        assert component.component_type == "zigbee"

    def test_it_serializes_zigbee_component_properly(self):
        component = ZigbeeComponent(
            key="zigbee",
            component_type="zigbee",
            network_state="joined",
            enabled=True,
            status={"network_state": "joined"},
            config={"enable": True},
            attrs={},
        )

        data = component.model_dump()
        assert data["key"] == "zigbee"
        assert data["network_state"] == "joined"
        assert data["enabled"] is True

        json_str = component.model_dump_json()
        assert "zigbee" in json_str
        assert "joined" in json_str


class TestWifiComponent:
    def test_it_creates_wifi_component_from_raw_data(self):

        raw_data = {
            "key": "wifi",
            "status": {
                "sta_ip": "192.168.1.100",
                "sta_ip6": ["fe80::1", "2001:db8::1"],
                "status": "got ip",
                "ssid": "MyNetwork",
                "bssid": "aa:bb:cc:dd:ee:ff",
                "rssi": -50,
            },
            "config": {},
            "attrs": {},
        }

        component = WifiComponent.from_raw_data(raw_data)

        assert component.key == "wifi"
        assert component.component_type == "wifi"
        assert component.sta_ip == "192.168.1.100"
        assert component.sta_ip6 == ["fe80::1", "2001:db8::1"]
        assert component.wifi_status == "got ip"
        assert component.ssid == "MyNetwork"
        assert component.bssid == "aa:bb:cc:dd:ee:ff"
        assert component.rssi == -50

    def test_it_creates_wifi_component_with_defaults(self):
        raw_data = {"key": "wifi", "status": {}, "config": {}, "attrs": {}}

        component = WifiComponent.from_raw_data(raw_data)

        assert component.sta_ip is None
        assert component.sta_ip6 == []
        assert component.wifi_status == "unknown"
        assert component.ssid is None
        assert component.bssid is None
        assert component.rssi == 0

    def test_it_creates_wifi_component_with_partial_data(self):
        raw_data = {
            "key": "wifi",
            "status": {"sta_ip": "192.168.1.50", "ssid": "TestNetwork"},
            "config": {},
            "attrs": {},
        }

        component = WifiComponent.from_raw_data(raw_data)

        assert component.sta_ip == "192.168.1.50"
        assert component.ssid == "TestNetwork"
        assert component.wifi_status == "unknown"
        assert component.rssi == 0


class TestWebSocketComponent:
    def test_it_creates_websocket_component_from_raw_data(self):
        raw_data = {
            "key": "ws",
            "status": {"connected": True},
            "config": {},
            "attrs": {},
        }

        component = WebSocketComponent.from_raw_data(raw_data)

        assert component.key == "ws"
        assert component.component_type == "ws"
        assert component.connected is True

    def test_it_creates_websocket_component_with_defaults(self):
        raw_data = {"key": "ws", "status": {}, "config": {}, "attrs": {}}

        component = WebSocketComponent.from_raw_data(raw_data)

        assert component.connected is False

    def test_it_creates_websocket_component_disconnected(self):
        raw_data = {
            "key": "ws",
            "status": {"connected": False},
            "config": {},
            "attrs": {},
        }

        component = WebSocketComponent.from_raw_data(raw_data)

        assert component.connected is False


class TestInputComponent:
    def test_it_creates_input_component_from_raw_data(self):
        raw_data = {
            "key": "input:0",
            "status": {"state": True},
            "config": {
                "type": "button",
                "name": "Test Input",
                "enable": True,
                "invert": False,
            },
            "attrs": {},
        }

        component = InputComponent.from_raw_data(raw_data)

        assert component.key == "input:0"
        assert component.component_type == "input"
        assert component.state is True
        assert component.input_type == "button"
        assert component.name == "Test Input"
        assert component.enabled is True
        assert component.inverted is False
        assert component.status == {"state": True}
        assert component.config == {
            "type": "button",
            "name": "Test Input",
            "enable": True,
            "invert": False,
        }

    def test_it_creates_input_component_with_defaults(self):
        raw_data = {"key": "input:0", "status": {}, "config": {}, "attrs": {}}

        component = InputComponent.from_raw_data(raw_data)

        assert component.key == "input:0"
        assert component.component_type == "input"
        assert component.state is False
        assert component.input_type == "switch"
        assert component.name is None
        assert component.enabled is False
        assert component.inverted is False

    def test_it_creates_input_component_with_partial_data(self):
        raw_data = {
            "key": "input:1",
            "status": {"state": False},
            "config": {"name": "Partial Input", "invert": True},
            "attrs": {},
        }

        component = InputComponent.from_raw_data(raw_data)

        assert component.key == "input:1"
        assert component.state is False
        assert component.input_type == "switch"
        assert component.name == "Partial Input"
        assert component.enabled is False
        assert component.inverted is True

    def test_it_creates_input_component_with_disabled_state(self):
        raw_data = {
            "key": "input:2",
            "status": {"state": True},
            "config": {"enable": False, "type": "button", "name": "Disabled Input"},
            "attrs": {},
        }

        component = InputComponent.from_raw_data(raw_data)

        assert component.key == "input:2"
        assert component.state is True
        assert component.input_type == "button"
        assert component.name == "Disabled Input"
        assert component.enabled is False
        assert component.inverted is False

    def test_it_handles_none_state_properly(self):
        raw_data = {
            "key": "input:3",
            "status": {"state": None},
            "config": {"type": "switch"},
            "attrs": {},
        }

        component = InputComponent.from_raw_data(raw_data)

        assert component.state is False

    def test_it_gets_available_actions_with_input_methods(self):
        component = InputComponent(key="input:0", component_type="input")
        all_methods = [
            "Input.GetStatus",
            "Input.SetConfig",
            "Switch.Toggle",
            "Light.Set",
        ]

        available_actions = component.get_available_actions(all_methods)

        assert "Input.GetStatus" in available_actions
        assert "Input.SetConfig" in available_actions
        assert "Switch.Toggle" not in available_actions
        assert "Light.Set" not in available_actions
        assert len(available_actions) == 2

    def test_it_gets_available_actions_with_no_input_methods(self):
        component = InputComponent(key="input:0", component_type="input")
        all_methods = ["Switch.Toggle", "Light.Set", "System.GetStatus"]

        available_actions = component.get_available_actions(all_methods)

        assert available_actions == []

    def test_it_gets_available_actions_with_empty_methods(self):
        component = InputComponent(key="input:0", component_type="input")
        all_methods = []

        available_actions = component.get_available_actions(all_methods)

        assert available_actions == []

    @pytest.mark.parametrize(
        "state_value,expected_state",
        [
            (True, True),
            (False, False),
            (None, False),
        ],
    )
    def test_it_handles_various_state_values(self, state_value, expected_state):
        raw_data = {
            "key": "input:test",
            "status": {"state": state_value},
            "config": {},
            "attrs": {},
        }

        component = InputComponent.from_raw_data(raw_data)

        assert component.state == expected_state
        assert component.key == "input:test"

    @pytest.mark.parametrize(
        "input_type,expected_type",
        [
            ("switch", "switch"),
            ("button", "button"),
            ("analog", "analog"),
            ("digital", "digital"),
            ("", "switch"),
            (None, "switch"),
            ("invalid", "invalid"),
        ],
    )
    def test_it_handles_various_input_types(self, input_type, expected_type):
        raw_data = {
            "key": "input:test",
            "status": {"state": True},
            "config": {"type": input_type} if input_type is not None else {},
            "attrs": {},
        }

        component = InputComponent.from_raw_data(raw_data)

        assert component.input_type == expected_type
        assert component.state


class TestComponentFactoryEnhancements:
    def test_it_creates_wifi_component_for_wifi_type(self):

        raw_data = {
            "key": "wifi",
            "status": {"sta_ip": "192.168.1.100", "status": "got ip"},
            "config": {},
            "attrs": {},
        }

        component = ComponentFactory.create_component(raw_data)

        assert isinstance(component, WifiComponent)
        assert component.key == "wifi"
        assert component.sta_ip == "192.168.1.100"

    def test_it_creates_websocket_component_for_ws_type(self):
        raw_data = {
            "key": "ws",
            "status": {"connected": True},
            "config": {},
            "attrs": {},
        }

        component = ComponentFactory.create_component(raw_data)

        assert isinstance(component, WebSocketComponent)
        assert component.key == "ws"
        assert component.connected is True

    def test_it_creates_input_component_for_input_type(self):
        raw_data = {
            "key": "input:0",
            "status": {"state": True},
            "config": {"type": "button", "name": "Test Input", "enable": True},
            "attrs": {},
        }

        component = ComponentFactory.create_component(raw_data)

        assert isinstance(component, InputComponent)
        assert component.key == "input:0"
        assert component.state is True
        assert component.input_type == "button"
        assert component.name == "Test Input"
        assert component.enabled is True

    def test_it_creates_component_from_status_only(self):
        status_data = {
            "sta_ip": "192.168.1.200",
            "status": "got ip",
            "ssid": "TestWifi",
        }

        component = ComponentFactory.create_component_from_status("wifi", status_data)

        assert isinstance(component, WifiComponent)
        assert component.key == "wifi"
        assert component.sta_ip == "192.168.1.200"
        assert component.ssid == "TestWifi"
        assert component.config == {}

    def test_it_creates_system_component_from_status_only(self):
        status_data = {
            "mac": "AA:BB:CC:DD:EE:FF",
            "uptime": 3600,
            "restart_required": False,
            "available_updates": {"version": "1.2.0"},
        }

        component = ComponentFactory.create_component_from_status("sys", status_data)

        assert component.key == "sys"
        assert component.component_type == "sys"
        assert component.status == status_data
        assert component.config == {}


class TestComponentIntegrationEnhancements:
    def test_it_verifies_wifi_component_inheritance(self):

        component = WifiComponent(
            key="wifi",
            component_type="wifi",
            sta_ip="192.168.1.100",
            wifi_status="got ip",
        )

        assert isinstance(component, Component)
        assert component.get_available_actions([]) == []

    def test_it_verifies_websocket_component_inheritance(self):
        component = WebSocketComponent(key="ws", component_type="ws", connected=True)

        assert isinstance(component, Component)
        assert component.get_available_actions([]) == []

    def test_it_verifies_input_component_inheritance(self):
        component = InputComponent(
            key="input:0",
            component_type="input",
            state=True,
            input_type="button",
            name="Test Input",
            enabled=True,
            inverted=False,
        )

        assert isinstance(component, Component)
        assert isinstance(component, InputComponent)
        assert component.key == "input:0"
        assert component.component_type == "input"
        assert component.state is True
        assert component.input_type == "button"

        input_methods = ["Input.GetStatus", "Input.SetConfig"]
        available_actions = component.get_available_actions(input_methods)
        assert len(available_actions) == 2
        assert "Input.GetStatus" in available_actions
        assert "Input.SetConfig" in available_actions

    def test_it_serializes_wifi_component_properly(self):
        component = WifiComponent(
            key="wifi",
            component_type="wifi",
            sta_ip="192.168.1.100",
            ssid="TestNetwork",
            wifi_status="got ip",
        )

        data = component.model_dump()
        assert data["key"] == "wifi"
        assert data["sta_ip"] == "192.168.1.100"
        assert data["ssid"] == "TestNetwork"

    def test_it_serializes_websocket_component_properly(self):
        component = WebSocketComponent(key="ws", component_type="ws", connected=True)

        data = component.model_dump()
        assert data["key"] == "ws"
        assert data["connected"] is True

    def test_it_serializes_input_component_properly(self):
        component = InputComponent(
            key="input:0",
            component_type="input",
            state=True,
            input_type="button",
            name="Test Input",
            enabled=True,
            inverted=False,
            status={"state": True},
            config={"type": "button", "name": "Test Input"},
        )

        data = component.model_dump()
        assert data["key"] == "input:0"
        assert data["state"] is True
        assert data["input_type"] == "button"
        assert data["name"] == "Test Input"
        assert data["enabled"] is True
        assert data["inverted"] is False

        json_str = component.model_dump_json()
        assert "input:0" in json_str
        assert "Test Input" in json_str
        assert "button" in json_str
