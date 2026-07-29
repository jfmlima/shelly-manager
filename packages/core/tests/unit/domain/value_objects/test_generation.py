from core.domain.value_objects.generation import Generation


class TestFromDeviceGen:
    def test_it_maps_gen_1_to_gen1(self):
        assert Generation.from_device_gen(1) is Generation.GEN1

    def test_it_maps_the_rpc_family_to_gen2(self):
        assert Generation.from_device_gen(2) is Generation.GEN2
        assert Generation.from_device_gen(3) is Generation.GEN2
        assert Generation.from_device_gen(4) is Generation.GEN2

    def test_it_returns_none_when_the_generation_is_unknown(self):
        # A device status without a gen means undetermined, never Gen1.
        assert Generation.from_device_gen(None) is None


class TestFromLabel:
    def test_it_parses_the_stored_backup_labels(self):
        assert Generation.from_label("gen1") is Generation.GEN1
        assert Generation.from_label("gen2") is Generation.GEN2

    def test_it_returns_none_for_an_unknown_label(self):
        assert Generation.from_label("gen3") is None


class TestFromShellyPayload:
    def test_it_treats_a_missing_gen_field_as_gen1(self):
        # Gen1 firmware omits gen from /shelly and identifies via type.
        assert Generation.from_shelly_payload({"type": "SHSW-1"}) is Generation.GEN1

    def test_it_maps_a_present_gen_field_to_gen2(self):
        assert Generation.from_shelly_payload({"gen": 2}) is Generation.GEN2
        assert Generation.from_shelly_payload({"gen": 3}) is Generation.GEN2
