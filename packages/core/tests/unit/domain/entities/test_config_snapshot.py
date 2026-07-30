import pytest
from core.domain.entities.config_snapshot import (
    CONFIGURABLE_COMPONENT_TYPES,
    EXPORTABLE_COMPONENT_TYPES,
    SCHEDULES_KEY,
    ComponentSnapshot,
    DeviceSnapshot,
    SnapshotDeviceInfo,
)

# A snapshot in the shape stored by every backup taken before this type existed:
# Gen2 components, a script with fetched code, a script without, and schedules.
GEN2_SNAPSHOT = {
    "device_info": {
        "device_name": "Test Device",
        "device_type": "SNSW-001P16EU",
        "firmware_version": "1.0.0",
        "mac_address": "AABBCCDDEEFF",
        "app_name": "Plus1PM",
    },
    "components": {
        "switch:0": {
            "type": "switch",
            "success": True,
            "config": {"id": 0, "name": "Relay"},
            "error": None,
        },
        "sys": {"type": "sys", "success": False, "config": None, "error": "boom"},
        "script:1": {
            "type": "script",
            "success": True,
            "config": {"id": 1},
            "error": None,
            "code": {"data": "print(1)"},
        },
        "script:2": {
            "type": "script",
            "success": True,
            "config": {"id": 2},
            "error": None,
        },
        "schedules": {
            "type": "schedule",
            "success": True,
            "config": {"jobs": [], "rev": 0},
            "error": None,
        },
    },
}

GEN1_SNAPSHOT = {
    "device_info": {
        "device_name": "Shelly 1",
        "device_type": "SHSW-1",
        "firmware_version": "1.14.0",
        "mac_address": "AABBCCDDEEFF",
        "app_name": None,
    },
    "components": {
        "switch:0": {
            "type": "switch",
            "success": True,
            "config": {"name": "Relay"},
            "error": None,
        },
        "legacy_settings": {
            "type": "legacy_settings",
            "success": True,
            "config": {"relays": [{"auto_off": 30}]},
            "error": None,
        },
    },
}


class TestSnapshotRoundTrip:
    @pytest.mark.parametrize("raw", [GEN2_SNAPSHOT, GEN1_SNAPSHOT])
    def test_it_round_trips_a_stored_snapshot_unchanged(self, raw):
        assert DeviceSnapshot.from_dict(raw).to_dict() == raw

    def test_it_omits_code_for_components_that_never_had_it(self):
        entry = ComponentSnapshot(key="switch:0", component_type="switch", success=True)

        assert "code" not in entry.to_dict()

    def test_it_reads_a_snapshot_missing_every_section(self):
        snapshot = DeviceSnapshot.from_dict({})

        assert snapshot.components == {}
        assert snapshot.device_info == SnapshotDeviceInfo()

    def test_it_keeps_a_corrupt_entry_as_a_failed_capture(self):
        # Dropping the key would make a restore report it as absent from the
        # backup, which is a different (and wrong) thing to tell the caller.
        snapshot = DeviceSnapshot.from_dict({"components": {"switch:0": "corrupt"}})

        entry = snapshot.components["switch:0"]
        assert entry.success is False
        assert entry.error == "unreadable snapshot entry"
        assert not entry.has_restorable_payload


class TestComponentSnapshot:
    def test_it_reports_a_captured_config_as_restorable(self):
        entry = ComponentSnapshot(
            key="switch:0", component_type="switch", success=True, config={}
        )

        assert entry.has_restorable_payload

    def test_it_rejects_a_failed_capture(self):
        entry = ComponentSnapshot(
            key="switch:0", component_type="switch", success=False, error="boom"
        )

        assert not entry.has_restorable_payload

    def test_it_rejects_a_script_whose_code_was_never_fetched(self):
        entry = ComponentSnapshot(
            key="script:1", component_type="script", success=True, config={"id": 1}
        )

        assert not entry.has_restorable_payload

    def test_it_accepts_a_script_with_an_empty_body(self):
        entry = ComponentSnapshot(
            key="script:1",
            component_type="script",
            success=True,
            config={"id": 1},
            code={"data": ""},
        )

        assert entry.script_code == ""
        assert entry.has_restorable_payload

    def test_it_ignores_a_code_block_of_the_wrong_shape(self):
        entry = ComponentSnapshot(
            key="script:1", component_type="script", success=True, code={"data": 42}
        )

        assert entry.script_code is None


class TestDeviceSnapshot:
    def test_it_is_restorable_when_any_component_is(self):
        snapshot = DeviceSnapshot.from_dict(GEN2_SNAPSHOT)

        assert snapshot.has_restorable_payload

    def test_it_is_not_restorable_when_nothing_was_captured(self):
        snapshot = DeviceSnapshot.from_dict(
            {"components": {"sys": {"type": "sys", "success": False, "config": None}}}
        )

        assert not snapshot.has_restorable_payload

    def test_it_exposes_the_raw_gen1_settings(self):
        snapshot = DeviceSnapshot.from_dict(GEN1_SNAPSHOT)

        assert snapshot.legacy_settings == {"relays": [{"auto_off": 30}]}

    def test_it_has_no_legacy_settings_when_the_capture_failed(self):
        snapshot = DeviceSnapshot.from_dict(
            {
                "components": {
                    "legacy_settings": {
                        "type": "legacy_settings",
                        "success": False,
                        "config": None,
                    }
                }
            }
        )

        assert snapshot.legacy_settings is None

    def test_it_has_no_legacy_settings_on_a_gen2_snapshot(self):
        snapshot = DeviceSnapshot.from_dict(GEN2_SNAPSHOT)

        assert snapshot.legacy_settings is None


class TestComponentTypeVocabulary:
    def test_it_allows_exporting_schedules(self):
        assert SCHEDULES_KEY in EXPORTABLE_COMPONENT_TYPES

    def test_it_exports_every_component_type_the_namespace_table_knows(self):
        from core.domain.value_objects.component_namespace import (
            known_component_types,
        )

        excluded = {"shelly", "schedule", "kvs", "http", "webhook"}
        assert known_component_types() - excluded <= EXPORTABLE_COMPONENT_TYPES

    def test_it_does_not_export_the_action_routing_pseudo_components(self):
        assert "shelly" not in EXPORTABLE_COMPONENT_TYPES
        assert "schedule" not in EXPORTABLE_COMPONENT_TYPES

    def test_it_does_not_export_the_service_namespaces(self):
        assert "kvs" not in EXPORTABLE_COMPONENT_TYPES
        assert "http" not in EXPORTABLE_COMPONENT_TYPES
        assert "webhook" not in EXPORTABLE_COMPONENT_TYPES

    def test_it_does_not_allow_configuring_schedules(self):
        assert SCHEDULES_KEY not in CONFIGURABLE_COMPONENT_TYPES

    def test_it_does_not_allow_configuring_energy_data_logs(self):
        assert "emdata" not in CONFIGURABLE_COMPONENT_TYPES
        assert "em1data" not in CONFIGURABLE_COMPONENT_TYPES

    def test_it_configures_every_other_exportable_type(self):
        assert CONFIGURABLE_COMPONENT_TYPES == EXPORTABLE_COMPONENT_TYPES - {
            SCHEDULES_KEY,
            "emdata",
            "em1data",
        }
