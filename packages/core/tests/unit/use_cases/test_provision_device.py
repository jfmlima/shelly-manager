"""Tests for ProvisionDeviceUseCase."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.domain.value_objects.provision_request import (
    APDeviceInfo,
    DetectDeviceRequest,
    ProvisionDeviceRequest,
)
from core.use_cases.provision_device import ProvisionDeviceUseCase


@pytest.fixture
def sample_device_info():
    return APDeviceInfo(
        device_id="shellyplus2pm-a8032ab636ec",
        mac="A8032AB636EC",
        model="SNSW-102P16EU",
        generation=2,
        firmware_version="1.0.0",
        auth_enabled=False,
        auth_domain="shellyplus2pm-a8032ab636ec",
        app="Plus2PM",
    )


@pytest.fixture
def sample_profile():
    return ProvisioningProfile(
        id=1,
        name="test-profile",
        wifi_ssid="TestNetwork",
        wifi_password="wifipass",
        mqtt_enabled=True,
        mqtt_server="mqtt.example.com:1883",
        mqtt_user="mqttuser",
        mqtt_password="mqttpass",
        mqtt_topic_prefix_template="home/{device_id}",
        auth_password="authpass",
        device_name_template="shelly-{mac_suffix}",
        timezone="Europe/Berlin",
        cloud_enabled=False,
        is_default=True,
    )


@pytest.fixture
def mock_rpc_client():
    client = AsyncMock()
    # Default: successful RPC response
    client.make_rpc_request.return_value = (
        {"result": {"restart_required": False}},
        0.1,
    )
    return client


@pytest.fixture
def mock_detector(sample_device_info):
    detector = AsyncMock()
    detector.detect.return_value = sample_device_info
    return detector


@pytest.fixture
def mock_profile_repo(sample_profile):
    repo = AsyncMock()
    repo.get.return_value = sample_profile
    repo.get_default.return_value = sample_profile
    return repo


@pytest.fixture
def mock_credentials_repo():
    return AsyncMock()


@pytest.fixture
def use_case(mock_rpc_client, mock_detector, mock_profile_repo, mock_credentials_repo):
    @asynccontextmanager
    async def profile_repo_factory():
        yield mock_profile_repo

    @asynccontextmanager
    async def credentials_repo_factory():
        yield mock_credentials_repo

    return ProvisionDeviceUseCase(
        rpc_client=mock_rpc_client,
        detector=mock_detector,
        profile_repository_factory=profile_repo_factory,
        credentials_repository_factory=credentials_repo_factory,
    )


class TestDetect:
    async def test_it_detects_device(self, use_case, mock_detector, sample_device_info):
        request = DetectDeviceRequest(device_ip="192.168.33.1")

        result = await use_case.detect(request)

        assert result.device_id == "shellyplus2pm-a8032ab636ec"
        assert result.mac == "A8032AB636EC"
        mock_detector.detect.assert_called_once_with("192.168.33.1", 5.0)


class TestExecute:
    async def test_it_provisions_device_successfully(
        self, use_case, mock_rpc_client, mock_credentials_repo
    ):
        request = ProvisionDeviceRequest(device_ip="192.168.33.1")

        result = await use_case.execute(request)

        assert result.success is True
        assert result.device_id == "shellyplus2pm-a8032ab636ec"
        assert result.device_mac == "A8032AB636EC"
        assert result.needs_verification is True

        # Check that all steps were attempted
        step_names = [s.name for s in result.steps_completed]
        assert "detect" in step_names
        assert "resolve_profile" in step_names
        assert "set_sys" in step_names
        assert "set_auth" in step_names
        assert "set_mqtt" in step_names
        assert "set_cloud" in step_names
        assert "set_wifi" in step_names

    async def test_it_stores_credentials_after_auth(
        self, use_case, mock_credentials_repo
    ):
        request = ProvisionDeviceRequest(device_ip="192.168.33.1")

        await use_case.execute(request)

        mock_credentials_repo.set.assert_called_once_with(
            mac="A8032AB636EC",
            username="admin",
            password="authpass",
            last_seen_ip="192.168.33.1",
        )

    async def test_it_fails_when_device_not_detected(self, use_case, mock_detector):
        from core.domain.entities.exceptions import DeviceNotFoundError

        mock_detector.detect.side_effect = DeviceNotFoundError(
            "192.168.33.1", "Not reachable"
        )

        request = ProvisionDeviceRequest(device_ip="192.168.33.1")
        result = await use_case.execute(request)

        assert result.success is False
        assert "detection failed" in (result.error or "").lower()
        assert len(result.steps_failed) == 1
        assert result.steps_failed[0].name == "detect"

    async def test_it_fails_when_no_profile_available(
        self, use_case, mock_profile_repo
    ):
        mock_profile_repo.get.return_value = None
        mock_profile_repo.get_default.return_value = None

        request = ProvisionDeviceRequest(device_ip="192.168.33.1")
        result = await use_case.execute(request)

        assert result.success is False
        assert "no provisioning profile" in (result.error or "").lower()

    async def test_it_continues_on_non_critical_failure(
        self, use_case, mock_rpc_client
    ):
        """Non-critical steps (sys, auth, mqtt, cloud) should not abort."""
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            method = args[1] if len(args) > 1 else kwargs.get("method", "")
            # Fail sys config
            if method == "Sys.SetConfig":
                raise Exception("Sys config failed")
            # Succeed everything else
            return ({"result": {"restart_required": False}}, 0.1)

        mock_rpc_client.make_rpc_request.side_effect = side_effect

        request = ProvisionDeviceRequest(device_ip="192.168.33.1")
        result = await use_case.execute(request)

        # Should still succeed overall since WiFi worked
        assert result.success is True
        failed_names = [s.name for s in result.steps_failed]
        assert "set_sys" in failed_names

    async def test_it_aborts_on_wifi_failure(self, use_case, mock_rpc_client):
        """WiFi failure is critical and should abort."""

        async def side_effect(*args, **kwargs):
            method = args[1] if len(args) > 1 else kwargs.get("method", "")
            if method == "WiFi.SetConfig":
                raise ValueError("WiFi config failed critically")
            return ({"result": {"restart_required": False}}, 0.1)

        mock_rpc_client.make_rpc_request.side_effect = side_effect

        request = ProvisionDeviceRequest(device_ip="192.168.33.1")
        result = await use_case.execute(request)

        assert result.success is False
        assert "wi-fi" in (result.error or "").lower()

    async def test_it_uses_profile_by_id(self, use_case, mock_profile_repo):
        request = ProvisionDeviceRequest(device_ip="192.168.33.1", profile_id=1)

        result = await use_case.execute(request)

        mock_profile_repo.get.assert_called_once_with(1)
        assert result.success is True

    async def test_it_uses_default_profile_when_no_id(
        self, use_case, mock_profile_repo
    ):
        request = ProvisionDeviceRequest(device_ip="192.168.33.1")

        result = await use_case.execute(request)

        mock_profile_repo.get_default.assert_called_once()
        assert result.success is True

    async def test_it_reboots_when_mqtt_configured(self, use_case, mock_rpc_client):
        """MQTT config always requires reboot."""

        async def side_effect(*args, **kwargs):
            method = args[1] if len(args) > 1 else kwargs.get("method", "")
            if method == "MQTT.SetConfig":
                return ({"result": {"restart_required": True}}, 0.1)
            return ({"result": {"restart_required": False}}, 0.1)

        mock_rpc_client.make_rpc_request.side_effect = side_effect

        request = ProvisionDeviceRequest(device_ip="192.168.33.1")
        result = await use_case.execute(request)

        assert result.success is True
        step_names = [s.name for s in result.steps_completed]
        assert "reboot" in step_names


class TestProvisionStepResults:
    async def test_it_reports_device_info_in_result(self, use_case):
        request = ProvisionDeviceRequest(device_ip="192.168.33.1")
        result = await use_case.execute(request)

        assert result.device_model == "SNSW-102P16EU"
        assert result.device_mac == "A8032AB636EC"
        assert result.generation == 2
