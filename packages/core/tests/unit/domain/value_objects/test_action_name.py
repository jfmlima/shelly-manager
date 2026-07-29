import pytest
from core.domain.value_objects.action_name import ActionName

DEVICE_METHODS = [
    "Switch.Toggle",
    "Sys.SetConfig",
    "Shelly.Reboot",
    "Shelly.ZigbeeClear",
    "Zigbee.GetStatus",
    "Wifi.SetConfig",
    "Mqtt.SetConfig",
    "EMData.GetStatus",
    "EM1Data.GetStatus",
]


class TestParse:
    def test_it_splits_a_qualified_name(self):
        assert ActionName.parse("Switch.Toggle") == ActionName(
            namespace="Switch", method="Toggle"
        )

    def test_it_keeps_a_nested_method_with_its_leading_namespace(self):
        assert ActionName.parse("Shelly.ZigbeeStartNetworkSteering") == ActionName(
            namespace="Shelly", method="ZigbeeStartNetworkSteering"
        )

    @pytest.mark.parametrize("raw", ["Toggle", "", ".Toggle", "Switch."])
    def test_it_rejects_anything_without_both_halves(self, raw):
        assert ActionName.parse(raw) is None


class TestOf:
    def test_it_keeps_a_bare_action_unqualified(self):
        action = ActionName.of("Toggle")

        assert action == ActionName(method="Toggle")
        assert action.namespace is None
        assert action.qualified is None

    def test_it_takes_an_already_qualified_action_as_given(self):
        assert ActionName.of("Switch.Toggle") == ActionName(
            namespace="Switch", method="Toggle"
        )

    def test_it_keeps_the_method_of_a_qualified_action(self):
        assert ActionName.of("EMData.GetStatus").method == "GetStatus"

    def test_it_recognises_legacy_actions(self):
        assert ActionName.of("Legacy.Toggle").is_legacy is True

    def test_it_does_not_mistake_a_gen2_action_for_a_legacy_one(self):
        assert ActionName.of("Toggle").is_legacy is False


class TestResolve:
    @pytest.mark.parametrize(
        "component_key,action,expected",
        [
            ("wifi", "WiFi.SetConfig", "Wifi.SetConfig"),
            ("wifi", "SetConfig", "Wifi.SetConfig"),
            ("mqtt", "MQTT.SetConfig", "Mqtt.SetConfig"),
            ("emdata:0", "GetStatus", "EMData.GetStatus"),
            ("switch:0", "Switch.Toggle", "Switch.Toggle"),
        ],
    )
    def test_it_returns_the_spelling_the_device_reported(
        self, component_key, action, expected
    ):
        action_name = ActionName.of(action)

        assert action_name.resolve(component_key, DEVICE_METHODS) == expected

    @pytest.mark.parametrize(
        "component_key,action,expected",
        [
            ("sys", "Reboot", "Shelly.Reboot"),
            ("sys", "SetConfig", "Sys.SetConfig"),
            ("zigbee", "ZigbeeClear", "Shelly.ZigbeeClear"),
            ("zigbee", "GetStatus", "Zigbee.GetStatus"),
        ],
    )
    def test_it_reaches_every_method_the_component_owns(
        self, component_key, action, expected
    ):
        action_name = ActionName.of(action)

        assert action_name.resolve(component_key, DEVICE_METHODS) == expected

    @pytest.mark.parametrize(
        "component_key,action",
        [
            ("wifi", "Shelly.FactoryReset"),
            ("wifi", "Shelly.Reboot"),
            ("switch:0", "Shelly.FactoryReset"),
            ("mqtt", "Switch.Toggle"),
            ("zigbee", "FactoryReset"),
            ("zigbee", "Shelly.FactoryReset"),
            ("zigbee", "Reboot"),
        ],
    )
    def test_it_refuses_a_method_the_component_does_not_own(
        self, component_key, action
    ):
        methods = [*DEVICE_METHODS, "Shelly.FactoryReset"]
        action_name = ActionName.of(action)

        assert action_name.resolve(component_key, methods) is None

    def test_it_rejects_a_method_the_device_did_not_report(self):
        action_name = ActionName.of("Nonsense")

        assert action_name.resolve("switch:0", DEVICE_METHODS) is None

    def test_it_prefers_the_components_own_namespace_when_both_carry_the_method(self):
        methods = ["Shelly.GetConfig", "Sys.GetConfig"]
        action_name = ActionName.of("GetConfig")

        assert action_name.resolve("sys", methods) == "Sys.GetConfig"


class TestResolveWithoutAMethodList:
    def test_it_does_not_second_guess_a_device_that_reported_nothing(self):
        action_name = ActionName.of("Toggle")

        assert action_name.resolve("switch:0", []) == "Switch.Toggle"

    def test_it_keeps_a_namespace_the_component_addresses(self):
        action_name = ActionName.of("Shelly.Reboot")

        assert action_name.resolve("sys", []) == "Shelly.Reboot"

    @pytest.mark.parametrize(
        "component_key,action",
        [
            ("wifi", "Shelly.FactoryReset"),
            ("wifi", "shelly.factoryreset"),
            ("zigbee", "Shelly.FactoryReset"),
            ("switch:0", "Shelly.Reboot"),
        ],
    )
    def test_it_refuses_an_unowned_qualified_call_rather_than_rewriting_it(
        self, component_key, action
    ):
        assert ActionName.of(action).resolve(component_key, []) is None


class TestResolveHonoursAnExplicitNamespace:

    METHODS = [
        "Sys.GetConfig",
        "Shelly.FactoryReset",
        "Shelly.ZigbeeClear",
        "Zigbee.GetStatus",
        "Wifi.SetConfig",
        "Switch.Toggle",
    ]

    @pytest.mark.parametrize(
        "component_key,action",
        [
            ("sys", "Sys.FactoryReset"),
            ("sys", "Zigbee.FactoryReset"),
            ("wifi", "Switch.SetConfig"),
            ("zigbee", "Switch.ZigbeeClear"),
            ("zigbee", "Zigbee.ZigbeeClear"),
        ],
    )
    def test_it_refuses_rather_than_substituting_another_method(
        self, component_key, action
    ):
        assert ActionName.of(action).resolve(component_key, self.METHODS) is None

    @pytest.mark.parametrize(
        "component_key,action,expected",
        [
            ("sys", "Shelly.FactoryReset", "Shelly.FactoryReset"),
            ("zigbee", "Shelly.ZigbeeClear", "Shelly.ZigbeeClear"),
            ("wifi", "WIFI.SetConfig", "Wifi.SetConfig"),
        ],
    )
    def test_it_still_honours_a_namespace_the_component_owns(
        self, component_key, action, expected
    ):
        assert ActionName.of(action).resolve(component_key, self.METHODS) == expected

    def test_a_bare_method_still_searches_the_components_namespaces(self):
        assert ActionName.of("FactoryReset").resolve("sys", self.METHODS) == (
            "Shelly.FactoryReset"
        )

    def test_it_keeps_an_owned_qualified_action_working_without_a_method_list(self):
        assert ActionName.of("Shelly.ZigbeeClear").resolve("zigbee", []) == (
            "Shelly.ZigbeeClear"
        )

    def test_it_refuses_an_unowned_qualified_action_without_a_method_list(self):
        assert ActionName.of("Shelly.FactoryReset").resolve("wifi", []) is None

    def test_a_bare_method_still_works_without_a_method_list(self):
        assert ActionName.of("SetConfig").resolve("wifi", []) == "Wifi.SetConfig"


class TestMethodNamesContainingDots:
    """Newer firmware reports names like BLE.CloudRelay.List."""

    METHODS = ["BLE.CloudRelay.List", "BLE.GetConfig"]

    def test_it_splits_only_at_the_first_dot(self):
        action = ActionName.of("BLE.CloudRelay.List")

        assert action.namespace == "BLE"
        assert action.method == "CloudRelay.List"

    def test_a_listed_name_pasted_back_still_resolves(self):
        action = ActionName.of("BLE.CloudRelay.List")

        assert action.resolve("ble", self.METHODS) == "BLE.CloudRelay.List"

    def test_dropping_the_leading_namespace_reads_as_another_one_and_is_refused(self):
        action = ActionName.of("CloudRelay.List")

        assert action.namespace == "CloudRelay"
        assert action.resolve("ble", self.METHODS) is None
