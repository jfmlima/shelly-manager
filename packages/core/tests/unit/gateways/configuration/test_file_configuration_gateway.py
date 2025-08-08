"""
Tests for FileConfigurationGateway (read-only operations).
"""

import json
import os
import tempfile

import pytest
from core.gateways.configuration.file_configuration_gateway import (
    FileConfigurationGateway,
)


class TestFileConfigurationGateway:

    @pytest.fixture
    def temp_config_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {
                "device_ips": ["192.168.1.100", "192.168.1.101"],
                "predefined_ranges": [{"start": "192.168.1.1", "end": "192.168.1.5"}],
                "timeout": 5.0,
                "max_workers": 100,
            }
            json.dump(config_data, f)
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def gateway_with_temp_file(self, temp_config_file):
        return FileConfigurationGateway(config_file_path=temp_config_file)

    @pytest.fixture
    def gateway_with_nonexistent_file(self):
        return FileConfigurationGateway(
            config_file_path="/nonexistent/path/config.json"
        )

    async def test_it_creates_gateway_with_default_config_path(self):
        gateway = FileConfigurationGateway()

        assert gateway._config_file_path == os.path.join(os.getcwd(), "config.json")

    async def test_it_creates_gateway_with_custom_config_path(self):
        custom_path = "/custom/path/config.json"
        gateway = FileConfigurationGateway(config_file_path=custom_path)

        assert gateway._config_file_path == custom_path

    async def test_it_gets_config_from_existing_file(self, gateway_with_temp_file):
        config = await gateway_with_temp_file.get_config()

        assert config["device_ips"] == ["192.168.1.100", "192.168.1.101"]
        assert config["predefined_ranges"] == [
            {"start": "192.168.1.1", "end": "192.168.1.5"}
        ]
        assert config["timeout"] == 5.0
        assert config["max_workers"] == 100

    async def test_it_returns_default_config_when_file_not_exists(
        self, gateway_with_nonexistent_file
    ):
        config = await gateway_with_nonexistent_file.get_config()

        assert config["device_ips"] == []
        assert config["predefined_ranges"] == [
            {"start": "192.168.1.1", "end": "192.168.1.10"}
        ]
        assert config["timeout"] == 3.0
        assert config["max_workers"] == 50
        assert config["update_channel"] == "stable"

    async def test_it_returns_default_config_when_file_corrupted(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            gateway = FileConfigurationGateway(config_file_path=temp_path)
            config = await gateway.get_config()

            assert config["device_ips"] == []
            assert config["timeout"] == 3.0
        finally:
            os.unlink(temp_path)

    async def test_it_gets_predefined_ips_from_device_list(
        self, gateway_with_temp_file
    ):
        ips = await gateway_with_temp_file.get_predefined_ips()

        assert "192.168.1.100" in ips
        assert "192.168.1.101" in ips
        assert "192.168.1.1" in ips
        assert "192.168.1.5" in ips
        assert len([ip for ip in ips if ip.startswith("192.168.1.")]) >= 7

    async def test_it_generates_ips_from_predefined_ranges(self):
        config_data = {
            "device_ips": [],
            "predefined_ranges": [
                {"start": "10.0.0.1", "end": "10.0.0.3"},
                {"start": "172.16.0.1", "end": "172.16.0.2"},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            gateway = FileConfigurationGateway(config_file_path=temp_path)
            ips = await gateway.get_predefined_ips()

            assert "10.0.0.1" in ips
            assert "10.0.0.2" in ips
            assert "10.0.0.3" in ips
            assert "172.16.0.1" in ips
            assert "172.16.0.2" in ips
            assert len(ips) == 5
        finally:
            os.unlink(temp_path)

    async def test_it_handles_empty_predefined_ranges(self):
        config_data = {"device_ips": ["192.168.1.100"], "predefined_ranges": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            gateway = FileConfigurationGateway(config_file_path=temp_path)
            ips = await gateway.get_predefined_ips()

            assert ips == ["192.168.1.100"]
        finally:
            os.unlink(temp_path)

    async def test_it_handles_malformed_ip_ranges(self):
        config_data = {
            "device_ips": [],
            "predefined_ranges": [
                {"start": "invalid.ip", "end": "192.168.1.5"},
                {"start": "192.168.1.1", "end": "malformed"},
                {"start": "192.168.1", "end": "192.168.1.5"},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            gateway = FileConfigurationGateway(config_file_path=temp_path)
            ips = await gateway.get_predefined_ips()

            assert ips == []
        finally:
            os.unlink(temp_path)

    async def test_it_handles_single_ip_range(self):
        config_data = {
            "device_ips": [],
            "predefined_ranges": [{"start": "192.168.1.5", "end": "192.168.1.5"}],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            gateway = FileConfigurationGateway(config_file_path=temp_path)
            ips = await gateway.get_predefined_ips()

            assert ips == ["192.168.1.5"]
        finally:
            os.unlink(temp_path)

    async def test_it_handles_large_ip_range(self):
        config_data = {
            "device_ips": [],
            "predefined_ranges": [{"start": "192.168.1.1", "end": "192.168.1.254"}],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            gateway = FileConfigurationGateway(config_file_path=temp_path)
            ips = await gateway.get_predefined_ips()

            assert len(ips) == 254
            assert "192.168.1.1" in ips
            assert "192.168.1.254" in ips
        finally:
            os.unlink(temp_path)

    async def test_it_handles_empty_device_ips_and_ranges(self):
        config_data = {"device_ips": [], "predefined_ranges": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            gateway = FileConfigurationGateway(config_file_path=temp_path)
            ips = await gateway.get_predefined_ips()

            assert ips == []
        finally:
            os.unlink(temp_path)
