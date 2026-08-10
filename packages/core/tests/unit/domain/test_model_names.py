from core.domain.model_names import MODEL_NAMES, get_model_name


class TestGetModelName:
    def test_it_returns_marketing_name_for_known_model(self):
        assert get_model_name("SNSW-102P16EU") == "Shelly Plus 2PM"
        assert get_model_name("SHSW-1") == "Shelly 1"
        assert get_model_name("S4SW-001P8EU") == "Shelly 1PM Mini Gen4"
        assert get_model_name("SPSW-101XE16EU") == "Shelly Pro 1"

    def test_it_returns_none_for_unknown_model(self):
        assert get_model_name("NOT-A-MODEL") is None

    def test_it_returns_none_for_missing_model(self):
        assert get_model_name(None) is None
        assert get_model_name("") is None

    def test_it_ignores_surrounding_whitespace(self):
        assert get_model_name(" SNSW-102P16EU ") == "Shelly Plus 2PM"

    def test_mapping_keys_are_normalized(self):
        for model in MODEL_NAMES:
            assert model == model.strip()
