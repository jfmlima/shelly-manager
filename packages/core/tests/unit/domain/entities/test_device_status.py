from core.domain.entities.components import (
    CloudComponent,
    SwitchComponent,
    SystemComponent,
    ZigbeeComponent,
)
from core.domain.entities.device_status import DeviceStatus


class TestDeviceStatusComponents:
    def test_it_creates_device_status_with_zigbee_from_status_data(self):
        device_ip = "192.168.1.100"
        response_data = {
            "components": [
                {
                    "key": "switch:0",
                    "status": {"output": True},
                    "config": {"name": "Test Switch"},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
            "offset": 0,
        }
        status_data = {
            "switch:0": {"output": True},
            "zigbee": {"network_state": "joined"},
        }

        device_status = DeviceStatus.from_raw_response(
            device_ip, response_data, status_data=status_data
        )

        assert device_status.device_ip == device_ip
        assert len(device_status.components) == 2

        switch_comp = device_status.get_component_by_key("switch:0")
        assert switch_comp is not None
        assert isinstance(switch_comp, SwitchComponent)

        zigbee_comp = device_status.get_component_by_key("zigbee")
        assert zigbee_comp is not None
        assert isinstance(zigbee_comp, ZigbeeComponent)
        assert zigbee_comp.network_state == "joined"

    def test_it_creates_device_status_without_zigbee_data(self):
        device_ip = "192.168.1.100"
        response_data = {
            "components": [
                {
                    "key": "switch:0",
                    "status": {"output": True},
                    "config": {"name": "Test Switch"},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
            "offset": 0,
        }

        device_status = DeviceStatus.from_raw_response(device_ip, response_data)

        assert device_status.device_ip == device_ip
        assert len(device_status.components) == 1

        switch_comp = device_status.get_component_by_key("switch:0")
        assert switch_comp is not None
        assert isinstance(switch_comp, SwitchComponent)

        zigbee_comp = device_status.get_component_by_key("zigbee")
        assert zigbee_comp is None

    def test_it_gets_zigbee_info_method(self):
        zigbee_comp = ZigbeeComponent(
            key="zigbee", component_type="zigbee", network_state="joined", enabled=True
        )

        device_status = DeviceStatus(
            device_ip="192.168.1.100", components=[zigbee_comp]
        )

        zigbee_info = device_status.get_zigbee_info()
        assert zigbee_info is not None
        assert isinstance(zigbee_info, ZigbeeComponent)
        assert zigbee_info.network_state == "joined"
        assert zigbee_info.enabled is True

    def test_it_gets_zigbee_info_method_no_zigbee(self):
        device_status = DeviceStatus(device_ip="192.168.1.100", components=[])

        zigbee_info = device_status.get_zigbee_info()
        assert zigbee_info is None

    def test_it_includes_zigbee_info_in_device_summary(self):
        system_comp = SystemComponent(
            key="sys",
            component_type="sys",
            device_name="Test Device",
            mac_address="AA:BB:CC:DD:EE:FF",
            firmware_version="20231201-123456",
        )

        cloud_comp = CloudComponent(
            key="cloud", component_type="cloud", connected=True, enabled=True
        )

        zigbee_comp = ZigbeeComponent(
            key="zigbee", component_type="zigbee", network_state="joined", enabled=True
        )

        device_status = DeviceStatus(
            device_ip="192.168.1.100", components=[system_comp, cloud_comp, zigbee_comp]
        )

        summary = device_status.get_device_summary()

        assert "zigbee_connected" in summary
        assert "zigbee_network_state" in summary
        assert summary["zigbee_connected"] is True
        assert summary["zigbee_network_state"] == "joined"

    def test_it_handles_device_summary_no_zigbee(self):
        device_status = DeviceStatus(device_ip="192.168.1.100", components=[])

        summary = device_status.get_device_summary()

        assert "zigbee_connected" in summary
        assert "zigbee_network_state" in summary
        assert summary["zigbee_connected"] is False
        assert summary["zigbee_network_state"] is None

    def test_it_creates_zigbee_component_from_status_data(self):
        device_ip = "192.168.1.100"
        response_data = {"components": []}
        status_data = {"zigbee": {"network_state": "left", "some_other_field": "value"}}

        device_status = DeviceStatus.from_raw_response(
            device_ip, response_data, status_data=status_data
        )

        zigbee_comp = device_status.get_zigbee_info()
        assert zigbee_comp is not None
        assert zigbee_comp.key == "zigbee"
        assert zigbee_comp.component_type == "zigbee"
        assert zigbee_comp.network_state == "left"
        assert zigbee_comp.status == {
            "network_state": "left",
            "some_other_field": "value",
        }
        assert zigbee_comp.config == {}
        assert zigbee_comp.attrs == {}


class TestDeviceStatusCore:
    """Test core DeviceStatus functionality."""

    def test_it_maintains_existing_convenience_methods(self):
        switch_comp = SwitchComponent(
            key="switch:0", component_type="switch", output=True, power=100.0
        )

        device_status = DeviceStatus(
            device_ip="192.168.1.100", components=[switch_comp]
        )

        switches = device_status.get_switches()
        assert len(switches) == 1
        assert switches[0].output is True

        switch_by_key = device_status.get_component_by_key("switch:0")
        assert switch_by_key is not None
        assert isinstance(switch_by_key, SwitchComponent)

    def test_it_includes_expected_device_summary_fields(self):
        system_comp = SystemComponent(
            key="sys", component_type="sys", device_name="Test Device"
        )

        device_status = DeviceStatus(
            device_ip="192.168.1.100", components=[system_comp]
        )

        summary = device_status.get_device_summary()

        assert "device_name" in summary
        assert "mac_address" in summary
        assert "firmware_version" in summary
        assert "cloud_connected" in summary
        assert "switch_count" in summary
        assert "input_count" in summary
        assert "cover_count" in summary

    def test_it_creates_device_status_with_device_info_data(self):
        device_ip = "192.168.1.100"
        response_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {},
                    "config": {"device": {"name": "Old Name"}},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
        }
        device_info_data = {
            "name": "New Device Name",
            "model": "SNSW-001X16EU",
            "fw_id": "20231026-112640/v1.14.1-ga898e3a",
            "mac": "AA:BB:CC:DD:EE:FF",
            "app": "switch",
        }

        device_status = DeviceStatus.from_raw_response(
            device_ip, response_data, device_info_data=device_info_data
        )

        assert device_status.device_name == "New Device Name"
        assert device_status.device_type == "SNSW-001X16EU"
        assert device_status.firmware_version == "20231026-112640/v1.14.1-ga898e3a"
        assert device_status.mac_address == "AA:BB:CC:DD:EE:FF"
        assert device_status.app_name == "switch"

    def test_it_uses_device_info_data_in_summary(self):
        device_ip = "192.168.1.100"
        response_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {},
                    "config": {"device": {"name": "Old Name"}},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
        }
        device_info_data = {
            "name": "Fresh Device Name",
            "model": "SNSW-001X16EU",
            "fw_id": "20231026-112640/v1.14.1-ga898e3a",
            "mac": "FF:EE:DD:CC:BB:AA",
            "app": "switch",
        }

        device_status = DeviceStatus.from_raw_response(
            device_ip, response_data, device_info_data=device_info_data
        )

        summary = device_status.get_device_summary()

        assert summary["device_name"] == "Fresh Device Name"
        assert summary["mac_address"] == "FF:EE:DD:CC:BB:AA"
        assert summary["firmware_version"] == "20231026-112640/v1.14.1-ga898e3a"

    def test_it_uses_sys_component_when_device_info_missing(self):
        device_ip = "192.168.1.100"
        response_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {
                        "mac": "AA:BB:CC:DD:EE:FF",
                    },
                    "config": {
                        "device": {
                            "name": "Sys Component Name",
                            "fw_id": "20230913-112003/v1.14.0-gcb84623",
                        }
                    },
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
        }

        device_status = DeviceStatus.from_raw_response(device_ip, response_data)

        summary = device_status.get_device_summary()

        assert summary["device_name"] == "Sys Component Name"
        assert summary["mac_address"] == "AA:BB:CC:DD:EE:FF"
        assert summary["firmware_version"] == "20230913-112003/v1.14.0-gcb84623"

    def test_it_handles_partial_device_info_data(self):
        device_ip = "192.168.1.100"
        response_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {
                        "mac": "AA:BB:CC:DD:EE:FF",
                    },
                    "config": {
                        "device": {
                            "name": "Sys Name",
                            "fw_id": "20230913-112003",
                        }
                    },
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
        }
        device_info_data = {
            "name": "DeviceInfo Name",
        }

        device_status = DeviceStatus.from_raw_response(
            device_ip, response_data, device_info_data=device_info_data
        )

        summary = device_status.get_device_summary()

        assert summary["device_name"] == "DeviceInfo Name"
        assert summary["mac_address"] == "AA:BB:CC:DD:EE:FF"
        assert summary["firmware_version"] == "20230913-112003"

    def test_it_handles_empty_device_info_data(self):
        device_ip = "192.168.1.100"
        response_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {
                        "mac": "AA:BB:CC:DD:EE:FF",
                    },
                    "config": {"device": {"name": "Sys Name"}},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
        }
        device_info_data = {}

        device_status = DeviceStatus.from_raw_response(
            device_ip, response_data, device_info_data=device_info_data
        )

        summary = device_status.get_device_summary()

        assert summary["device_name"] == "Sys Name"
        assert summary["mac_address"] == "AA:BB:CC:DD:EE:FF"


class TestDeviceStatusMerging:
    """Test device status merging from components and status endpoints."""

    def test_it_merges_components_and_status_data(self):
        """Test merging data from get_components and get_status."""
        device_ip = "192.168.1.100"

        # Data from get_components (with config)
        components_data = {
            "components": [
                {
                    "key": "switch:0",
                    "status": {"output": True, "apower": 50.0},
                    "config": {"name": "Main Switch", "power_limit": 2800},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        # Data from get_status (with additional components)
        status_data = {
            "switch:0": {"output": True, "apower": 50.0},  # Overlapping with components
            "sys": {  # Missing from components
                "mac": "AA:BB:CC:DD:EE:FF",
                "uptime": 3600,
                "restart_required": False,
            },
            "wifi": {  # Missing from components
                "sta_ip": "192.168.1.100",
                "status": "got ip",
                "ssid": "MyNetwork",
                "rssi": -45,
            },
            "ws": {  # Missing from components
                "connected": False,
            },
        }

        device_status = DeviceStatus.from_raw_response(
            device_ip, components_data, status_data=status_data
        )

        # Should have all components: switch (from components) + sys, wifi, ws (from status)
        assert len(device_status.components) == 4

        # Check switch component (from components with config)
        switch = device_status.get_component_by_key("switch:0")
        assert switch is not None
        assert switch.config["name"] == "Main Switch"  # Config preserved
        assert switch.config["power_limit"] == 2800

        # Check system component (from status only)
        sys_comp = device_status.get_system_info()
        assert sys_comp is not None
        assert sys_comp.mac_address == "AA:BB:CC:DD:EE:FF"
        assert sys_comp.uptime == 3600

        # Check wifi component (from status only)
        wifi_comp = device_status.get_wifi_info()
        assert wifi_comp is not None
        assert wifi_comp.sta_ip == "192.168.1.100"
        assert wifi_comp.ssid == "MyNetwork"
        assert wifi_comp.rssi == -45

        # Check websocket component (from status only)
        ws_comp = device_status.get_websocket_info()
        assert ws_comp is not None
        assert ws_comp.connected is False

    def test_it_handles_status_only_without_components(self):
        """Test handling status data when get_components fails."""
        device_ip = "192.168.1.100"

        # Empty components data (get_components failed)
        components_data = {"components": [], "cfg_rev": 0, "total": 0}

        # Rich status data
        status_data = {
            "sys": {"mac": "AA:BB:CC:DD:EE:FF", "uptime": 7200},
            "wifi": {"sta_ip": "192.168.1.200", "status": "got ip"},
            "cloud": {"connected": True},
            "zigbee": {"network_state": "joined"},
        }

        device_status = DeviceStatus.from_raw_response(
            device_ip, components_data, status_data=status_data
        )

        # Should create components from status data only
        assert len(device_status.components) == 4
        assert device_status.get_system_info() is not None
        assert device_status.get_wifi_info() is not None
        assert device_status.get_cloud_info() is not None
        assert device_status.get_zigbee_info() is not None

    def test_it_includes_wifi_info_in_device_summary(self):
        """Test that device summary includes WiFi information."""
        device_ip = "192.168.1.100"
        components_data = {"components": [], "cfg_rev": 0, "total": 0}
        status_data = {
            "wifi": {
                "sta_ip": "192.168.1.150",
                "status": "got ip",
                "ssid": "TestNetwork",
                "rssi": -30,
            },
            "ws": {"connected": True},
        }

        device_status = DeviceStatus.from_raw_response(
            device_ip, components_data, status_data=status_data
        )

        summary = device_status.get_device_summary()

        assert summary["wifi_connected"] is True
        assert summary["wifi_ssid"] == "TestNetwork"
        assert summary["wifi_ip"] == "192.168.1.150"
        assert summary["wifi_rssi"] == -30
        assert summary["websocket_connected"] is True

    def test_it_handles_missing_status_data_gracefully(self):
        """Test handling when get_status returns None or fails."""
        device_ip = "192.168.1.100"
        components_data = {
            "components": [
                {
                    "key": "switch:0",
                    "status": {"output": False},
                    "config": {"name": "Test Switch"},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        # No status data (get_status failed)
        device_status = DeviceStatus.from_raw_response(
            device_ip, components_data, status_data=None
        )

        # Should still work with just components data
        assert len(device_status.components) == 1
        assert device_status.get_component_by_key("switch:0") is not None

        # WiFi info should be None since no status data
        assert device_status.get_wifi_info() is None
        assert device_status.get_websocket_info() is None

        # Summary should handle missing info gracefully
        summary = device_status.get_device_summary()
        assert summary["wifi_connected"] is False
        assert summary["wifi_ssid"] is None
        assert summary["websocket_connected"] is False

    def test_it_creates_zigbee_component_from_status_only(self):
        """Test creating zigbee component when only in status data."""
        device_ip = "192.168.1.100"
        components_data = {"components": [], "cfg_rev": 0, "total": 0}

        # Status data with zigbee
        status_data = {
            "zigbee": {"network_state": "joined"},
            "sys": {"mac": "AA:BB:CC:DD:EE:FF"},
        }

        device_status = DeviceStatus.from_raw_response(
            device_ip, components_data, status_data=status_data
        )

        # Should have sys and zigbee from status
        assert len(device_status.components) == 2
        zigbee_comp = device_status.get_zigbee_info()
        assert zigbee_comp is not None
        assert zigbee_comp.network_state == "joined"
