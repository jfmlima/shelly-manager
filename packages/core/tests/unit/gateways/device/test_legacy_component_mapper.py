import pytest
from core.domain.entities.components import SwitchComponent
from core.gateways.device.legacy_component_mapper import LegacyComponentMapper
from pydantic import ValidationError


@pytest.fixture
def mapper():
    return LegacyComponentMapper()


def _switch_config(mapper, relay_settings):
    """Map a single-relay Gen1 device and return its switch:0 config."""
    components = mapper.map(
        {"mac": "AABBCCDDEEFF", "type": "SHSW-1"},
        {"relays": [{"ison": False}]},
        {"relays": [relay_settings]},
    )
    switch = next(c for c in components if c["key"] == "switch:0")
    return switch["config"]


class TestLegacyAutoTimerMapping:
    @pytest.mark.parametrize(
        "value, expected_flag, expected_delay",
        [
            (0, False, 0.0),
            (0.5, True, 0.5),
            (30, True, 30.0),
            (True, True, None),
        ],
    )
    def test_it_maps_auto_off_seconds_to_flag_and_delay(
        self, mapper, value, expected_flag, expected_delay
    ):
        config = _switch_config(mapper, {"auto_off": value})

        assert config["auto_off"] is expected_flag
        if expected_delay is None:
            assert "auto_off_delay" not in config
        else:
            assert config["auto_off_delay"] == expected_delay

    @pytest.mark.parametrize(
        "value, expected_flag, expected_delay",
        [
            (0, False, 0.0),
            (30, True, 30.0),
            (True, True, None),
        ],
    )
    def test_it_maps_auto_on_seconds_to_flag_and_delay(
        self, mapper, value, expected_flag, expected_delay
    ):
        config = _switch_config(mapper, {"auto_on": value})

        assert config["auto_on"] is expected_flag
        if expected_delay is None:
            assert "auto_on_delay" not in config
        else:
            assert config["auto_on_delay"] == expected_delay

    def test_it_defaults_missing_auto_timer_to_false_without_delay(self, mapper):
        config = _switch_config(mapper, {})

        assert config["auto_on"] is False
        assert config["auto_off"] is False
        assert "auto_on_delay" not in config
        assert "auto_off_delay" not in config

    def test_it_treats_garbage_auto_timer_as_disabled(self, mapper):
        config = _switch_config(mapper, {"auto_on": "nonsense", "auto_off": None})

        assert config["auto_on"] is False
        assert config["auto_off"] is False
        assert "auto_on_delay" not in config
        assert "auto_off_delay" not in config


class TestSwitchComponentAcceptsMappedGen1Relay:
    def test_switch_component_accepts_mapped_relay_with_timer(self, mapper):
        components = mapper.map(
            {"mac": "AABBCCDDEEFF", "type": "SHSW-1"},
            {"relays": [{"ison": True}]},
            {"relays": [{"auto_off": 0.5, "auto_on": 30}]},
        )
        mapped_switch = next(c for c in components if c["key"] == "switch:0")

        component = SwitchComponent.from_raw_data(mapped_switch)

        assert component.auto_off is True
        assert component.auto_on is True
        # Delays live on the raw config dict, not as SwitchComponent fields.
        assert component.config["auto_off_delay"] == 0.5
        assert component.config["auto_on_delay"] == 30.0

    def test_raw_numeric_seconds_still_raise_at_the_component(self):
        # The component stays strict on purpose; only the mapper heals raw seconds.
        with pytest.raises(ValidationError):
            SwitchComponent.from_raw_data(
                {"key": "switch:0", "status": {}, "config": {"auto_off": 0.5}}
            )
