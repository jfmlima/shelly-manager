from datetime import datetime

from api.controllers.devices import (
    get_device_config,
    get_device_status,
    reboot_device,
    scan_devices,
    set_device_config,
    update_device,
)
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.entities.device_status import DeviceStatus
from core.domain.enums.enums import Status
from core.domain.value_objects.action_result import ActionResult
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.reboot_device import RebootDeviceUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase
from litestar.di import Provide
from litestar.testing import create_test_client


class TestDevicesController:

    def test_scan_devices_successfully(self):
        class MockScanDevicesUseCase(ScanDevicesUseCase):
            def __init__(self):
                pass

            async def execute(self, scan_request):
                device = DiscoveredDevice(
                    ip="192.168.1.100",
                    status=Status.DETECTED,
                    device_type="Shelly 1",
                    device_name="Test Device",
                    firmware_version="1.0.0",
                    response_time=0.5,
                    last_seen=datetime.now(),
                )
                return [device]

        with create_test_client(
            route_handlers=[scan_devices],
            dependencies={
                "scan_interactor": Provide(
                    lambda: MockScanDevicesUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/scan")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["ip"] == "192.168.1.100"
            assert data[0]["status"] == "detected"

    def test_update_device_successfully(self):
        class MockUpdateDeviceUseCase(UpdateDeviceFirmwareUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return ActionResult(
                    device_ip=request.device_ip,
                    success=True,
                    message="Update started",
                    action_type="firmware_update",
                )

        with create_test_client(
            route_handlers=[update_device],
            dependencies={
                "update_interactor": Provide(
                    lambda: MockUpdateDeviceUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post("/192.168.1.100/update")

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is True
            assert data["message"] == "Update started"

    def test_reboot_device_successfully(self):
        class MockRebootDeviceUseCase(RebootDeviceUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return ActionResult(
                    device_ip=request.device_ip,
                    success=True,
                    message="Reboot initiated",
                    action_type="reboot",
                )

        with create_test_client(
            route_handlers=[reboot_device],
            dependencies={
                "reboot_interactor": Provide(
                    lambda: MockRebootDeviceUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post("/192.168.1.100/reboot")

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is True
            assert data["message"] == "Reboot initiated"

    def test_get_device_status_successfully(self):
        class MockCheckDeviceStatusUseCase(CheckDeviceStatusUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return DeviceStatus(
                    device_ip=request.device_ip,
                    components=[],
                    total_components=0,
                )

        with create_test_client(
            route_handlers=[get_device_status],
            dependencies={
                "status_interactor": Provide(
                    lambda: MockCheckDeviceStatusUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/192.168.1.100/status")

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert "components" in data
            assert "summary" in data
            assert "firmware" in data

    def test_get_device_config_successfully(self):
        class MockGetConfigurationUseCase(GetConfigurationUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return {"relay": {"name": "Test Relay"}}

        with create_test_client(
            route_handlers=[get_device_config],
            dependencies={
                "get_config_interactor": Provide(
                    lambda: MockGetConfigurationUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/192.168.1.100/config")

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is True
            assert data["config"]["relay"]["name"] == "Test Relay"

    def test_set_device_config_successfully(self):
        class MockSetConfigurationUseCase(SetConfigurationUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return {"success": True, "message": "Configuration updated"}

        with create_test_client(
            route_handlers=[set_device_config],
            dependencies={
                "set_config_interactor": Provide(
                    lambda: MockSetConfigurationUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/192.168.1.100/config",
                json={"config": {"relay": {"name": "New Name"}}},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is True
            assert data["message"] == "Configuration updated"

    def test_get_device_config_fails(self):
        class MockGetConfigurationUseCase(GetConfigurationUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                raise Exception("Device not reachable")

        with create_test_client(
            route_handlers=[get_device_config],
            dependencies={
                "get_config_interactor": Provide(
                    lambda: MockGetConfigurationUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/192.168.1.100/config")

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is False
            assert data["error"] == "Device not reachable"

    def test_set_device_config_fails(self):
        class MockSetConfigurationUseCase(SetConfigurationUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                raise Exception("Permission denied")

        with create_test_client(
            route_handlers=[set_device_config],
            dependencies={
                "set_config_interactor": Provide(
                    lambda: MockSetConfigurationUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/192.168.1.100/config",
                json={"config": {"relay": {"name": "New Name"}}},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is False
            assert data["error"] == "Permission denied"
