from core.gateways.device.component_type_mapping import (
    COMPONENT_TYPE_TO_API,
    get_api_component_type,
)


def test_it_maps_known_component_types():
    assert get_api_component_type("switch") == "Switch"
    assert get_api_component_type("light") == "Light"
    assert get_api_component_type("temperature") == "Temperature"
    assert get_api_component_type("em") == "EM"
    assert get_api_component_type("wifi") == "Wifi"


def test_it_handles_case_insensitivity():
    assert get_api_component_type("SWITCH") == "Switch"
    assert get_api_component_type("Light") == "Light"
    assert get_api_component_type("wIfI") == "Wifi"


def test_it_falls_back_to_title_case_for_unknown_types():
    assert get_api_component_type("unknown") == "Unknown"
    assert get_api_component_type("custom_sensor") == "Custom_Sensor"


def test_it_contains_expected_mappings():
    assert "switch" in COMPONENT_TYPE_TO_API
    assert "cover" in COMPONENT_TYPE_TO_API
    assert "input" in COMPONENT_TYPE_TO_API
    assert COMPONENT_TYPE_TO_API["switch"] == "Switch"
