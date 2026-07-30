import pytest
from core.domain.value_objects.component_namespace import ComponentNamespace

DEVICE_METHODS = [
    "Switch.Toggle",
    "Switch.Set",
    "Sys.GetConfig",
    "Sys.SetConfig",
    "Shelly.Reboot",
    "Shelly.ListMethods",
    "Wifi.SetConfig",
    "Wifi.Scan",
    "Mqtt.SetConfig",
    "EM.GetStatus",
    "EM1.GetStatus",
    "EMData.GetStatus",
    "EMData.ResetCounters",
    "EM1Data.GetStatus",
    "WS.SetConfig",
]


def actions_for(component_type: str, methods: list[str]) -> list[str]:
    return ComponentNamespace.for_component_type(component_type).actions_in(methods)


class TestForComponentType:
    @pytest.mark.parametrize(
        "component_type,expected",
        [
            ("switch", "Switch"),
            ("emdata", "EMData"),
            ("em1data", "EM1Data"),
            ("wifi", "Wifi"),
            ("mqtt", "Mqtt"),
            ("ws", "WS"),
            ("sys", "Sys"),
        ],
    )
    def test_it_knows_the_namespace_a_component_qualifies_as(
        self, component_type, expected
    ):
        assert ComponentNamespace.for_component_type(component_type).qualifies_as == (
            expected
        )

    def test_it_ignores_the_casing_of_the_component_type(self):
        assert ComponentNamespace.for_component_type("EMData").qualifies_as == "EMData"

    def test_it_guesses_for_a_component_type_it_does_not_know(self):
        assert ComponentNamespace.for_component_type("newthing").qualifies_as == (
            "Newthing"
        )

    @pytest.mark.parametrize(
        "component_type,method,owns",
        [
            ("sys", "Sys.GetConfig", True),
            ("sys", "Shelly.FactoryReset", True),
            ("switch", "Switch.Toggle", True),
            ("switch", "Shelly.FactoryReset", False),
            ("wifi", "Shelly.FactoryReset", False),
            ("wifi", "wifi.setconfig", True),
            ("zigbee", "Shelly.ZigbeeClear", True),
            ("zigbee", "Shelly.FactoryReset", False),
            ("em", "EMData.GetStatus", False),
        ],
    )
    def test_it_knows_which_methods_a_component_owns(
        self, component_type, method, owns
    ):
        assert ComponentNamespace.for_component_type(component_type).owns(method) is (
            owns
        )


class TestActionsIn:
    @pytest.mark.parametrize(
        "component_type,expected",
        [
            ("switch", ["Switch.Toggle", "Switch.Set"]),
            ("wifi", ["Wifi.SetConfig", "Wifi.Scan"]),
            ("mqtt", ["Mqtt.SetConfig"]),
            ("emdata", ["EMData.GetStatus", "EMData.ResetCounters"]),
            ("em1data", ["EM1Data.GetStatus"]),
            ("em", ["EM.GetStatus"]),
            ("em1", ["EM1.GetStatus"]),
        ],
    )
    def test_it_selects_only_the_methods_of_that_type(self, component_type, expected):
        assert actions_for(component_type, DEVICE_METHODS) == expected

    def test_it_gives_the_system_component_both_its_namespaces(self):
        assert actions_for("sys", DEVICE_METHODS) == [
            "Sys.GetConfig",
            "Sys.SetConfig",
            "Shelly.Reboot",
            "Shelly.ListMethods",
        ]

    def test_it_matches_regardless_of_the_casing_the_device_reports(self):
        assert actions_for("wifi", ["WiFi.SetConfig", "WIFI.Scan"]) == [
            "WiFi.SetConfig",
            "WIFI.Scan",
        ]

    def test_it_surfaces_the_websocket_components_own_methods(self):
        assert actions_for("ws", DEVICE_METHODS) == ["WS.SetConfig"]

    def test_it_gives_zigbee_the_shelly_prefixed_method_that_belongs_to_it(self):
        methods = ["Zigbee.GetStatus", "Shelly.ZigbeeClear", "Shelly.Reboot"]

        assert actions_for("zigbee", methods) == [
            "Zigbee.GetStatus",
            "Shelly.ZigbeeClear",
        ]

    def test_it_falls_back_to_the_type_name_for_unknown_components(self):
        methods = ["Newthing.GetStatus", "Switch.Toggle"]

        assert actions_for("newthing", methods) == ["Newthing.GetStatus"]

    @pytest.mark.parametrize(
        "component_key,namespace",
        [
            ("boolean:200", "Boolean"),
            ("button:200", "Button"),
            ("enum:200", "Enum"),
            ("group:200", "Group"),
            ("number:200", "Number"),
            ("text:200", "Text"),
        ],
    )
    def test_it_names_the_virtual_component_types_rather_than_guessing(
        self, component_key, namespace
    ):
        component_type = component_key.split(":")[0]

        assert ComponentNamespace.for_component_type(component_type).qualifies_as == (
            namespace
        )

    def test_it_returns_nothing_when_the_device_reported_nothing(self):
        assert actions_for("switch", []) == []


class TestOwnershipIsNotALoosePrefix:
    def test_it_gives_zigbee_its_named_shelly_method_and_nothing_else(self):
        namespace = ComponentNamespace.for_component_type("zigbee")

        assert namespace.owns("Shelly.ZigbeeClear") is True
        assert namespace.owns("Shelly.ZigbeeAnything") is False
        assert namespace.owns("Shelly.FactoryReset") is False

    def test_it_matches_the_device_casing_from_an_exact_entry(self):
        namespace = ComponentNamespace.for_component_type("zigbee")

        assert namespace.actions_in(["shelly.zigbeeclear"]) == ["shelly.zigbeeclear"]

    def test_it_matches_a_whole_family_from_a_namespace_prefix_entry(self):
        namespace = ComponentNamespace.for_component_type("zigbee")

        assert namespace.actions_in(["Zigbee.GetStatus", "Zigbee.SetConfig"]) == [
            "Zigbee.GetStatus",
            "Zigbee.SetConfig",
        ]
