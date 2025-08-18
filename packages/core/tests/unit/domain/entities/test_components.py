"""
Tests for component entities.
"""

import pytest
from core.domain.entities.components import (
    Component,
    SwitchComponent,
    InputComponent,
    CoverComponent,
    SystemComponent,
    CloudComponent,
    ZigbeeComponent,
    ComponentFactory,
)


class TestZigbeeComponent:
    """Test ZigbeeComponent creation and functionality."""

    def test_it_creates_zigbee_component_from_raw_data(self):
        """Test creating a ZigbeeComponent from raw data."""
        raw_data = {
            "key": "zigbee",
            "status": {"network_state": "joined"},
            "config": {"enable": True},
            "attrs": {}
        }
        
        component = ZigbeeComponent.from_raw_data(raw_data)
        
        assert component.key == "zigbee"
        assert component.component_type == "zigbee"
        assert component.network_state == "joined"
        assert component.enabled is True
        assert component.status == {"network_state": "joined"}
        assert component.config == {"enable": True}

    def test_it_creates_zigbee_component_with_defaults(self):
        """Test ZigbeeComponent with default values."""
        raw_data = {
            "key": "zigbee",
            "status": {},
            "config": {},
            "attrs": {}
        }
        
        component = ZigbeeComponent.from_raw_data(raw_data)
        
        assert component.network_state == "unknown"
        assert component.enabled is False

    def test_it_creates_zigbee_component_with_network_state(self):
        """Test ZigbeeComponent with different network states."""
        raw_data = {
            "key": "zigbee",
            "status": {"network_state": "left"},
            "config": {"enable": False},
            "attrs": {}
        }
        
        component = ZigbeeComponent.from_raw_data(raw_data)
        
        assert component.network_state == "left"
        assert component.enabled is False


class TestComponentFactory:
    """Test ComponentFactory with Zigbee components."""

    def test_it_creates_zigbee_component_for_zigbee_type(self):
        """Test that ComponentFactory creates ZigbeeComponent for zigbee type."""
        raw_data = {
            "key": "zigbee",
            "status": {"network_state": "joined"},
            "config": {"enable": True},
            "attrs": {}
        }
        
        component = ComponentFactory.create_component(raw_data)
        
        assert isinstance(component, ZigbeeComponent)
        assert component.network_state == "joined"
        assert component.enabled is True

    def test_it_creates_switch_component_for_switch_type(self):
        """Test that ComponentFactory still creates SwitchComponent for switch type."""
        raw_data = {
            "key": "switch:0",
            "status": {"output": True},
            "config": {"name": "Test Switch"},
            "attrs": {}
        }
        
        component = ComponentFactory.create_component(raw_data)
        
        assert isinstance(component, SwitchComponent)
        assert component.output is True
        assert component.name == "Test Switch"

    def test_it_creates_base_component_for_unknown_type(self):
        """Test that ComponentFactory creates base Component for unknown types."""
        raw_data = {
            "key": "unknown:component",
            "status": {"some_field": "value"},
            "config": {},
            "attrs": {}
        }
        
        component = ComponentFactory.create_component(raw_data)
        
        assert isinstance(component, Component)
        assert component.key == "unknown:component"
        assert component.component_type == "unknown"


class TestComponentIntegration:
    """Test component integration and type safety."""

    def test_it_verifies_zigbee_component_inheritance(self):
        """Test that ZigbeeComponent properly inherits from Component."""
        component = ZigbeeComponent(
            key="zigbee",
            component_type="zigbee",
            network_state="joined",
            enabled=True
        )
        
        assert isinstance(component, Component)
        assert isinstance(component, ZigbeeComponent)
        assert component.key == "zigbee"
        assert component.component_type == "zigbee"

    def test_it_serializes_zigbee_component_properly(self):
        """Test that ZigbeeComponent can be serialized properly."""
        component = ZigbeeComponent(
            key="zigbee",
            component_type="zigbee",
            network_state="joined",
            enabled=True,
            status={"network_state": "joined"},
            config={"enable": True},
            attrs={}
        )
        
        data = component.model_dump()
        assert data["key"] == "zigbee"
        assert data["network_state"] == "joined"
        assert data["enabled"] is True
        
        json_str = component.model_dump_json()
        assert "zigbee" in json_str
        assert "joined" in json_str
