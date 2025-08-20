"""
Tests for DeviceStatus entity with Zigbee integration.
"""

from core.domain.entities.components import (
    CloudComponent,
    SwitchComponent,
    SystemComponent,
    ZigbeeComponent,
)
from core.domain.entities.device_status import DeviceStatus


class TestDeviceStatusZigbeeIntegration:
    """Test DeviceStatus with Zigbee component integration."""

    def test_it_creates_device_status_with_zigbee_data(self):
        """Test creating DeviceStatus with Zigbee data."""
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
        zigbee_data = {"network_state": "joined"}

        device_status = DeviceStatus.from_raw_response(
            device_ip, response_data, zigbee_data
        )

        assert device_status.device_ip == device_ip
        assert len(device_status.components) == 2  # switch + zigbee

        switch_comp = device_status.get_component_by_key("switch:0")
        assert switch_comp is not None
        assert isinstance(switch_comp, SwitchComponent)

        zigbee_comp = device_status.get_component_by_key("zigbee")
        assert zigbee_comp is not None
        assert isinstance(zigbee_comp, ZigbeeComponent)
        assert zigbee_comp.network_state == "joined"

    def test_it_creates_device_status_without_zigbee_data(self):
        """Test creating DeviceStatus without Zigbee data."""
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
        assert len(device_status.components) == 1  # only switch

        switch_comp = device_status.get_component_by_key("switch:0")
        assert switch_comp is not None
        assert isinstance(switch_comp, SwitchComponent)

        zigbee_comp = device_status.get_component_by_key("zigbee")
        assert zigbee_comp is None

    def test_it_gets_zigbee_info_method(self):
        """Test the get_zigbee_info convenience method."""
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
        """Test get_zigbee_info when no zigbee component exists."""
        device_status = DeviceStatus(device_ip="192.168.1.100", components=[])

        zigbee_info = device_status.get_zigbee_info()
        assert zigbee_info is None

    def test_it_includes_zigbee_info_in_device_summary(self):
        """Test that device summary includes Zigbee connectivity information."""
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
        """Test device summary when no zigbee component exists."""
        device_status = DeviceStatus(device_ip="192.168.1.100", components=[])

        summary = device_status.get_device_summary()

        assert "zigbee_connected" in summary
        assert "zigbee_network_state" in summary
        assert summary["zigbee_connected"] is False
        assert summary["zigbee_network_state"] is None

    def test_it_creates_zigbee_component_from_raw_data(self):
        """Test that zigbee component is created with correct structure."""
        device_ip = "192.168.1.100"
        response_data = {"components": []}
        zigbee_data = {"network_state": "left", "some_other_field": "value"}

        device_status = DeviceStatus.from_raw_response(
            device_ip, response_data, zigbee_data
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


class TestDeviceStatusBackwardCompatibility:
    """Test that existing DeviceStatus functionality remains unchanged."""

    def test_it_maintains_existing_convenience_methods(self):
        """Test that existing convenience methods continue to work."""
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

    def test_it_maintains_existing_device_summary_fields(self):
        """Test that existing device summary fields are preserved."""
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
