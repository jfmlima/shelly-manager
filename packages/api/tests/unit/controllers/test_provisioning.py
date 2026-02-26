"""Tests for the provisioning API controllers."""

from api.controllers.provisioning import (
    ProvisioningController,
    ProvisioningProfilesController,
)
from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.domain.value_objects.provision_request import (
    APDeviceInfo,
    ProvisionResult,
    ProvisionStep,
)
from core.use_cases.manage_provisioning_profiles import (
    ManageProvisioningProfilesUseCase,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)
from core.use_cases.provision_device import ProvisionDeviceUseCase
from litestar.di import Provide
from litestar.testing import create_test_client


class TestProvisioningProfilesController:
    def test_list_profiles_empty(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def list_profiles(self):
                return []

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/profiles")

            assert response.status_code == 200
            assert response.json() == []

    def test_list_profiles_returns_profiles(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def list_profiles(self):
                return [
                    ProvisioningProfile(
                        id=1,
                        name="home",
                        wifi_ssid="MyNetwork",
                        wifi_password="secret",
                        mqtt_enabled=True,
                        mqtt_server="mqtt.local:1883",
                        is_default=True,
                    ),
                    ProvisioningProfile(
                        id=2,
                        name="office",
                        wifi_ssid="OfficeWifi",
                        is_default=False,
                    ),
                ]

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/profiles")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "home"
            assert data[0]["wifi_ssid"] == "MyNetwork"
            assert data[0]["is_default"] is True
            assert data[0]["has_wifi_password"] is True
            assert data[0]["mqtt_enabled"] is True
            assert data[0]["mqtt_server"] == "mqtt.local:1883"
            assert data[1]["name"] == "office"
            assert data[1]["is_default"] is False

    def test_create_profile_successfully(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def create_profile(self, profile):
                return ProvisioningProfile(
                    id=1,
                    name=profile.name,
                    wifi_ssid=profile.wifi_ssid,
                    wifi_password=profile.wifi_password,
                    mqtt_enabled=profile.mqtt_enabled,
                    is_default=True,
                    created_at=1700000000,
                )

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/profiles",
                json={
                    "name": "test-profile",
                    "wifi_ssid": "TestNet",
                    "wifi_password": "pass123",
                    "mqtt_enabled": False,
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "test-profile"
            assert data["wifi_ssid"] == "TestNet"
            assert data["has_wifi_password"] is True
            assert data["is_default"] is True

    def test_create_profile_duplicate_returns_409(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def create_profile(self, profile):
                raise ProfileAlreadyExistsError(profile.name)

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/profiles",
                json={"name": "existing-profile"},
            )

            assert response.status_code == 409

    def test_get_profile_successfully(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def get_profile(self, profile_id):
                return ProvisioningProfile(
                    id=profile_id,
                    name="my-profile",
                    wifi_ssid="MyNet",
                    auth_password="secret",
                    is_default=False,
                )

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/profiles/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "my-profile"
            assert data["has_auth_password"] is True

    def test_get_profile_not_found_returns_404(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def get_profile(self, profile_id):
                raise ProfileNotFoundError(profile_id)

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/profiles/999")

            assert response.status_code == 404

    def test_update_profile_successfully(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def get_profile(self, profile_id):
                return ProvisioningProfile(
                    id=profile_id,
                    name="old-name",
                    wifi_ssid="OldNet",
                    is_default=False,
                )

            async def update_profile(self, profile):
                return ProvisioningProfile(
                    id=profile.id,
                    name=profile.name,
                    wifi_ssid=profile.wifi_ssid,
                    is_default=profile.is_default,
                    updated_at=1700000100,
                )

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.put(
                "/profiles/1",
                json={"name": "new-name", "wifi_ssid": "NewNet"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "new-name"
            assert data["wifi_ssid"] == "NewNet"

    def test_update_profile_not_found_returns_404(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def get_profile(self, profile_id):
                raise ProfileNotFoundError(profile_id)

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.put(
                "/profiles/999",
                json={"name": "test"},
            )

            assert response.status_code == 404

    def test_delete_profile_successfully(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def delete_profile(self, profile_id):
                return None

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.delete("/profiles/1")

            assert response.status_code == 204

    def test_delete_profile_not_found_returns_404(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def delete_profile(self, profile_id):
                raise ProfileNotFoundError(profile_id)

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.delete("/profiles/999")

            assert response.status_code == 404

    def test_set_default_profile_successfully(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def set_default_profile(self, profile_id):
                return None

            async def get_profile(self, profile_id):
                return ProvisioningProfile(
                    id=profile_id,
                    name="my-profile",
                    is_default=True,
                )

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post("/profiles/1/set-default")

            assert response.status_code == 201
            data = response.json()
            assert data["is_default"] is True

    def test_set_default_profile_not_found_returns_404(self):
        class MockManageProfiles(ManageProvisioningProfilesUseCase):
            def __init__(self):
                pass

            async def set_default_profile(self, profile_id):
                raise ProfileNotFoundError(profile_id)

        with create_test_client(
            route_handlers=[ProvisioningProfilesController],
            dependencies={
                "manage_profiles_use_case": Provide(
                    lambda: MockManageProfiles(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post("/profiles/999/set-default")

            assert response.status_code == 404


class TestProvisioningController:
    def test_detect_device_successfully(self):
        class MockProvisionDevice(ProvisionDeviceUseCase):
            def __init__(self):
                pass

            async def detect(self, request):
                return APDeviceInfo(
                    device_id="shellyplus1pm-a4cf12f45678",
                    mac="A4CF12F45678",
                    model="SNSW-001P16EU",
                    generation=2,
                    firmware_version="1.4.4",
                    auth_enabled=False,
                    auth_domain="shellyplus1pm-a4cf12f45678",
                    app="Plus1PM",
                )

        with create_test_client(
            route_handlers=[ProvisioningController],
            dependencies={
                "provision_device_use_case": Provide(
                    lambda: MockProvisionDevice(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/detect",
                json={"device_ip": "192.168.33.1", "timeout": 5.0},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["device_id"] == "shellyplus1pm-a4cf12f45678"
            assert data["mac"] == "A4CF12F45678"
            assert data["model"] == "SNSW-001P16EU"
            assert data["generation"] == 2
            assert data["firmware_version"] == "1.4.4"
            assert data["auth_enabled"] is False
            assert data["app"] == "Plus1PM"

    def test_detect_device_not_found(self):
        class MockProvisionDevice(ProvisionDeviceUseCase):
            def __init__(self):
                pass

            async def detect(self, request):
                from core.domain.entities.exceptions import DeviceNotFoundError

                raise DeviceNotFoundError(
                    "192.168.33.1",
                    "Device at 192.168.33.1 did not respond within 5.0s",
                )

        with create_test_client(
            route_handlers=[ProvisioningController],
            dependencies={
                "provision_device_use_case": Provide(
                    lambda: MockProvisionDevice(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/detect",
                json={"device_ip": "192.168.33.1"},
            )

            assert response.status_code == 404
            data = response.json()
            assert "192.168.33.1" in data["detail"]
            assert "did not respond" in data["detail"]

    def test_detect_device_communication_error(self):
        class MockProvisionDevice(ProvisionDeviceUseCase):
            def __init__(self):
                pass

            async def detect(self, request):
                from core.domain.entities.exceptions import (
                    DeviceCommunicationError,
                )

                raise DeviceCommunicationError(
                    "192.168.33.1",
                    "Connection refused",
                    "Failed to connect to device at 192.168.33.1",
                )

        with create_test_client(
            route_handlers=[ProvisioningController],
            dependencies={
                "provision_device_use_case": Provide(
                    lambda: MockProvisionDevice(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/detect",
                json={"device_ip": "192.168.33.1"},
            )

            assert response.status_code == 502
            data = response.json()
            assert "192.168.33.1" in data["detail"]

    def test_provision_device_successfully(self):
        class MockProvisionDevice(ProvisionDeviceUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return ProvisionResult(
                    success=True,
                    device_id="shellyplus1pm-a4cf12f45678",
                    device_model="SNSW-001P16EU",
                    device_mac="A4CF12F45678",
                    generation=2,
                    steps_completed=[
                        ProvisionStep(
                            name="Sys.SetConfig",
                            success=True,
                            message="Device name set",
                        ),
                        ProvisionStep(
                            name="Shelly.SetAuth",
                            success=True,
                            message="Auth configured",
                        ),
                        ProvisionStep(
                            name="MQTT.SetConfig",
                            success=True,
                            message="MQTT configured",
                            restart_required=True,
                        ),
                        ProvisionStep(
                            name="WiFi.STA.SetConfig",
                            success=True,
                            message="WiFi configured",
                        ),
                    ],
                    steps_failed=[],
                    needs_verification=True,
                )

        with create_test_client(
            route_handlers=[ProvisioningController],
            dependencies={
                "provision_device_use_case": Provide(
                    lambda: MockProvisionDevice(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/provision",
                json={"device_ip": "192.168.33.1", "profile_id": 1},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["device_id"] == "shellyplus1pm-a4cf12f45678"
            assert data["device_mac"] == "A4CF12F45678"
            assert data["generation"] == 2
            assert len(data["steps_completed"]) == 4
            assert data["steps_completed"][0]["name"] == "Sys.SetConfig"
            assert data["steps_completed"][2]["restart_required"] is True
            assert data["steps_failed"] == []
            assert data["needs_verification"] is True

    def test_provision_device_with_failures(self):
        class MockProvisionDevice(ProvisionDeviceUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return ProvisionResult(
                    success=False,
                    device_id="shellyplus1pm-a4cf12f45678",
                    device_model="SNSW-001P16EU",
                    device_mac="A4CF12F45678",
                    generation=2,
                    steps_completed=[
                        ProvisionStep(
                            name="Sys.SetConfig",
                            success=True,
                            message="Device name set",
                        ),
                    ],
                    steps_failed=[
                        ProvisionStep(
                            name="WiFi.STA.SetConfig",
                            success=False,
                            message="WiFi config failed: timeout",
                        ),
                    ],
                    error="WiFi configuration failed",
                    needs_verification=False,
                )

        with create_test_client(
            route_handlers=[ProvisioningController],
            dependencies={
                "provision_device_use_case": Provide(
                    lambda: MockProvisionDevice(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/provision",
                json={"device_ip": "192.168.33.1"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is False
            assert len(data["steps_completed"]) == 1
            assert len(data["steps_failed"]) == 1
            assert data["error"] == "WiFi configuration failed"
            assert data["needs_verification"] is False

    def test_verify_provision_device_found(self):
        class MockProvisionDevice(ProvisionDeviceUseCase):
            def __init__(self):
                pass

            async def verify(self, device_mac, scan_targets, timeout=30.0):
                return "192.168.1.42"

        with create_test_client(
            route_handlers=[ProvisioningController],
            dependencies={
                "provision_device_use_case": Provide(
                    lambda: MockProvisionDevice(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/verify",
                json={
                    "device_mac": "A4CF12F45678",
                    "scan_targets": ["192.168.1.0/24"],
                    "timeout": 30.0,
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["found"] is True
            assert data["device_ip"] == "192.168.1.42"
            assert data["device_mac"] == "A4CF12F45678"

    def test_verify_provision_device_not_found(self):
        class MockProvisionDevice(ProvisionDeviceUseCase):
            def __init__(self):
                pass

            async def verify(self, device_mac, scan_targets, timeout=30.0):
                return None

        with create_test_client(
            route_handlers=[ProvisioningController],
            dependencies={
                "provision_device_use_case": Provide(
                    lambda: MockProvisionDevice(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/verify",
                json={
                    "device_mac": "A4CF12F45678",
                    "scan_targets": ["192.168.1.0/24"],
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["found"] is False
            assert data["device_ip"] is None
            assert data["device_mac"] == "A4CF12F45678"

    def test_detect_device_validates_ip(self):
        class MockProvisionDevice(ProvisionDeviceUseCase):
            def __init__(self):
                pass

        with create_test_client(
            route_handlers=[ProvisioningController],
            dependencies={
                "provision_device_use_case": Provide(
                    lambda: MockProvisionDevice(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/detect",
                json={"device_ip": "not-an-ip"},
            )

            assert response.status_code == 400
