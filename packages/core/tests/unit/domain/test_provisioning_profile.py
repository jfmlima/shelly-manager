"""Tests for ProvisioningProfile domain entity."""

from core.domain.entities.provisioning_profile import ProvisioningProfile


class TestProvisioningProfile:
    def test_it_creates_with_defaults(self):
        profile = ProvisioningProfile(name="test")

        assert profile.name == "test"
        assert profile.wifi_ssid is None
        assert profile.mqtt_enabled is False
        assert profile.cloud_enabled is False
        assert profile.is_default is False
        assert profile.id is None

    def test_it_creates_with_all_fields(self):
        profile = ProvisioningProfile(
            name="full",
            wifi_ssid="MyNetwork",
            wifi_password="pass123",
            mqtt_enabled=True,
            mqtt_server="broker:1883",
            mqtt_user="user",
            mqtt_password="mqttpass",
            mqtt_topic_prefix_template="home/{device_id}",
            auth_password="authpass",
            device_name_template="shelly-{mac_suffix}",
            timezone="Europe/Berlin",
            cloud_enabled=False,
            is_default=True,
            id=1,
        )

        assert profile.wifi_ssid == "MyNetwork"
        assert profile.mqtt_enabled is True
        assert profile.is_default is True
        assert profile.id == 1


class TestExpandTemplate:
    def test_it_expands_device_id(self):
        profile = ProvisioningProfile(name="test")
        result = profile.expand_template(
            "home/{device_id}",
            {"device_id": "shellyplus2pm-abc123", "mac": "A8032AB636EC"},
        )
        assert result == "home/shellyplus2pm-abc123"

    def test_it_expands_mac_suffix(self):
        profile = ProvisioningProfile(name="test")
        result = profile.expand_template(
            "shelly-{mac_suffix}",
            {"device_id": "test", "mac": "A8032AB636EC"},
        )
        assert result == "shelly-B636EC"

    def test_it_expands_multiple_placeholders(self):
        profile = ProvisioningProfile(name="test")
        result = profile.expand_template(
            "{app}-{mac_suffix}",
            {
                "device_id": "shellyplus2pm-abc",
                "model": "SNSW-102P16EU",
                "app": "Plus2PM",
                "mac": "A8032AB636EC",
            },
        )
        assert result == "Plus2PM-B636EC"

    def test_it_returns_none_for_none_template(self):
        profile = ProvisioningProfile(name="test")
        result = profile.expand_template(None, {"mac": "123456789012"})
        assert result is None

    def test_it_handles_empty_mac_gracefully(self):
        profile = ProvisioningProfile(name="test")
        result = profile.expand_template(
            "test-{mac_suffix}",
            {"device_id": "test", "mac": ""},
        )
        assert result == "test-"
