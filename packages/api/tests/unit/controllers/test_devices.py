from datetime import datetime

from api.controllers.devices import (
    bulk_apply_config,
    bulk_export_config,
    execute_bulk_operations,
    execute_component_action,
    get_component_actions,
    get_device_config,
    get_device_status,
    scan_devices,
    set_device_config,
)
from api.presentation.exceptions import DeviceNotFoundHTTPException
from core.domain.entities.device_status import DeviceStatus
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status
from core.domain.value_objects.action_result import ActionResult
from core.use_cases.bulk_operations import BulkOperationsUseCase
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.execute_component_action import ExecuteComponentActionUseCase
from core.use_cases.get_component_actions import GetComponentActionsUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
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
        class MockExecuteComponentActionUseCase(ExecuteComponentActionUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return ActionResult(
                    device_ip=request.device_ip,
                    success=True,
                    message="Update started",
                    action_type="OTA",
                )

        with create_test_client(
            route_handlers=[execute_component_action],
            dependencies={
                "execute_component_action_interactor": Provide(
                    lambda: MockExecuteComponentActionUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/192.168.1.100/components/sys/actions/OTA", json={"channel": "beta"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is True
            assert data["message"] == "Update started"
            assert data["component_key"] == "sys"
            assert data["action"] == "OTA"

    def test_reboot_device_successfully(self):
        class MockExecuteComponentActionUseCase(ExecuteComponentActionUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return ActionResult(
                    device_ip=request.device_ip,
                    success=True,
                    message="Reboot initiated",
                    action_type="Reboot",
                )

        with create_test_client(
            route_handlers=[execute_component_action],
            dependencies={
                "execute_component_action_interactor": Provide(
                    lambda: MockExecuteComponentActionUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/192.168.1.100/components/sys/actions/Reboot", json={}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is True
            assert data["message"] == "Reboot initiated"
            assert data["component_key"] == "sys"
            assert data["action"] == "Reboot"

    def test_get_component_actions_successfully(self):
        class MockGetComponentActionsUseCase(GetComponentActionsUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return {
                    "sys": ["Reboot", "OTA"],
                    "switch:0": ["Toggle", "On", "Off"],
                    "input:0": [],
                }

        with create_test_client(
            route_handlers=[get_component_actions],
            dependencies={
                "component_actions_interactor": Provide(
                    lambda: MockGetComponentActionsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.get("/192.168.1.100/components/actions")

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert "component_actions" in data
            assert "sys" in data["component_actions"]
            assert "Reboot" in data["component_actions"]["sys"]
            assert "OTA" in data["component_actions"]["sys"]
            assert "switch:0" in data["component_actions"]
            assert "Toggle" in data["component_actions"]["switch:0"]

    def test_execute_component_action_failure(self):
        class MockExecuteComponentActionUseCase(ExecuteComponentActionUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return ActionResult(
                    device_ip=request.device_ip,
                    success=False,
                    message="Action failed",
                    error="Device not responding",
                    action_type="Toggle",
                )

        with create_test_client(
            route_handlers=[execute_component_action],
            dependencies={
                "execute_component_action_interactor": Provide(
                    lambda: MockExecuteComponentActionUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/192.168.1.100/components/switch:0/actions/Toggle", json={}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ip"] == "192.168.1.100"
            assert data["success"] is False
            assert data["message"] == "Action failed"
            assert data["error"] == "Device not responding"
            assert data["component_key"] == "switch:0"
            assert data["action"] == "Toggle"

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

    def test_bulk_operations_update_successfully(self):
        from core.use_cases.bulk_operations import BulkOperationsUseCase

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

            async def execute_bulk_update(self, device_ips, channel="stable"):
                return [
                    ActionResult(
                        device_ip=ip,
                        success=True,
                        message="Update initiated",
                        action_type="Update",
                    )
                    for ip in device_ips
                ]

        with create_test_client(
            route_handlers=[execute_bulk_operations],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/bulk",
                json={
                    "device_ips": ["192.168.1.100", "192.168.1.101"],
                    "operation": "update",
                    "channel": "beta",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert all(result["success"] for result in data)
            assert all(result["operation"] == "update" for result in data)
            assert all(result["channel"] == "beta" for result in data)

    def test_bulk_operations_reboot_successfully(self):
        from core.use_cases.bulk_operations import BulkOperationsUseCase

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

            async def execute_bulk_reboot(self, device_ips):
                return [
                    ActionResult(
                        device_ip="192.168.1.100",
                        success=True,
                        message="Reboot initiated",
                        action_type="Reboot",
                    )
                ]

        with create_test_client(
            route_handlers=[execute_bulk_operations],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/bulk", json={"device_ips": ["192.168.1.100"], "operation": "reboot"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["success"]
            assert data[0]["action_type"] == "Reboot"
            assert data[0]["operation"] == "reboot"

    def test_bulk_operations_factory_reset_successfully(self):
        from core.use_cases.bulk_operations import BulkOperationsUseCase

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

            async def execute_bulk_factory_reset(self, device_ips):
                return [
                    ActionResult(
                        device_ip="192.168.1.100",
                        success=True,
                        message="Factory reset initiated",
                        action_type="FactoryReset",
                    )
                ]

        with create_test_client(
            route_handlers=[execute_bulk_operations],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/bulk",
                json={"device_ips": ["192.168.1.100"], "operation": "factory_reset"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["success"]
            assert data[0]["action_type"] == "FactoryReset"
            assert data[0]["operation"] == "factory_reset"

    def test_bulk_operations_validation_errors(self):
        from core.use_cases.bulk_operations import BulkOperationsUseCase

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

        with create_test_client(
            route_handlers=[execute_bulk_operations],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            # Test missing device_ips
            response = client.post("/bulk", json={"operation": "update"})
            assert response.status_code == 400
            assert "device_ips is required" in response.json()["detail"]

            # Test missing operation
            response = client.post("/bulk", json={"device_ips": ["192.168.1.100"]})
            assert response.status_code == 400
            assert "operation is required" in response.json()["detail"]

            # Test invalid operation
            response = client.post(
                "/bulk", json={"device_ips": ["192.168.1.100"], "operation": "invalid"}
            )
            assert response.status_code == 400
            assert "Unsupported operation: invalid" in response.json()["detail"]

    def test_get_device_status_returns_404_when_device_not_found(self):
        from datetime import datetime

        from litestar.response import Response

        def handle_device_not_found_exception(
            request, exc: DeviceNotFoundHTTPException
        ) -> Response:
            return Response(
                content={
                    "error": "Device Not Found",
                    "message": exc.detail,
                    "timestamp": datetime.now().isoformat(),
                    "ip": exc.device_ip,
                },
                status_code=404,
                media_type="application/json",
            )

        class MockCheckDeviceStatusUseCase(CheckDeviceStatusUseCase):
            def __init__(self):
                pass

            async def execute(self, request):
                return None  # Device not found

        with create_test_client(
            route_handlers=[get_device_status],
            dependencies={
                "status_interactor": Provide(
                    lambda: MockCheckDeviceStatusUseCase(), sync_to_thread=False
                )
            },
            exception_handlers={
                DeviceNotFoundHTTPException: handle_device_not_found_exception,
            },
        ) as client:
            response = client.get("/192.168.1.200/status")

            assert response.status_code == 404
            data = response.json()
            assert "Device Not Found" in data["error"]
            assert "192.168.1.200" in data["message"]
            assert data["ip"] == "192.168.1.200"

    def test_it_exports_bulk_config_successfully(self):

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

            async def export_bulk_config(self, device_ips, component_types):
                return {
                    "export_metadata": {
                        "timestamp": "2024-01-01T12:00:00Z",
                        "total_devices": len(device_ips),
                        "component_types": component_types,
                    },
                    "devices": {
                        "192.168.1.100": {
                            "device_info": {
                                "device_name": "Test Device",
                                "device_type": "shelly1pm",
                                "firmware_version": "20230913-112003",
                                "mac_address": "AA:BB:CC:DD:EE:FF",
                                "app_name": "switch",
                            },
                            "components": {
                                "switch:0": {
                                    "type": "switch",
                                    "success": True,
                                    "config": {
                                        "in_mode": "flip",
                                        "initial_state": "restore_last",
                                    },
                                    "error": None,
                                }
                            },
                        }
                    },
                }

        with create_test_client(
            route_handlers=[bulk_export_config],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/bulk/export-config",
                json={
                    "device_ips": ["192.168.1.100"],
                    "component_types": ["switch"],
                },
            )

            assert response.status_code == 201
            data = response.json()

            # Verify response structure
            assert "export_metadata" in data
            assert "devices" in data
            assert data["export_metadata"]["total_devices"] == 1
            assert data["export_metadata"]["component_types"] == ["switch"]

            # Verify device data
            device_data = data["devices"]["192.168.1.100"]
            assert device_data["device_info"]["device_name"] == "Test Device"
            assert "switch:0" in device_data["components"]
            assert device_data["components"]["switch:0"]["success"] is True

    def test_it_validates_bulk_export_config_errors(self):

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

        with create_test_client(
            route_handlers=[bulk_export_config],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            # Test missing device_ips
            response = client.post(
                "/bulk/export-config",
                json={"component_types": ["switch"]},
            )
            assert response.status_code == 400

            # Test missing component_types
            response = client.post(
                "/bulk/export-config",
                json={"device_ips": ["192.168.1.100"]},
            )
            assert response.status_code == 400

            # Test empty lists
            response = client.post(
                "/bulk/export-config",
                json={"device_ips": [], "component_types": []},
            )
            assert response.status_code == 400

            # Test invalid IP address
            response = client.post(
                "/bulk/export-config",
                json={"device_ips": ["invalid-ip"], "component_types": ["switch"]},
            )
            assert response.status_code == 400

            # Test invalid component type
            response = client.post(
                "/bulk/export-config",
                json={
                    "device_ips": ["192.168.1.100"],
                    "component_types": ["invalid_component"],
                },
            )
            assert response.status_code == 400

    def test_it_applies_bulk_config_successfully(self):

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

            async def apply_bulk_config(self, device_ips, component_type, config):
                return [
                    ActionResult(
                        success=True,
                        action_type="switch.SetConfig",
                        device_ip="192.168.1.100",
                        message="Configuration applied successfully",
                    ),
                    ActionResult(
                        success=True,
                        action_type="switch.SetConfig",
                        device_ip="192.168.1.101",
                        message="Configuration applied successfully",
                    ),
                ]

        with create_test_client(
            route_handlers=[bulk_apply_config],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/bulk/apply-config",
                json={
                    "device_ips": ["192.168.1.100", "192.168.1.101"],
                    "component_type": "switch",
                    "config": {"in_mode": "button", "initial_state": "off"},
                },
            )

            assert response.status_code == 201
            data = response.json()

            # Should return list of results
            assert isinstance(data, list)
            assert len(data) == 2

            # Verify result structure
            for result in data:
                assert "ip" in result
                assert "component_key" in result
                assert "success" in result
                assert "message" in result
                assert result["success"] is True

    def test_it_applies_bulk_config_with_failures(self):

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

            async def apply_bulk_config(self, device_ips, component_type, config):
                return [
                    ActionResult(
                        success=True,
                        action_type="switch.SetConfig",
                        device_ip="192.168.1.100",
                        message="Configuration applied successfully",
                    ),
                    ActionResult(
                        success=False,
                        action_type="switch.SetConfig",
                        device_ip="192.168.1.101",
                        message="Configuration apply failed",
                        error="Device unreachable",
                    ),
                ]

        with create_test_client(
            route_handlers=[bulk_apply_config],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            response = client.post(
                "/bulk/apply-config",
                json={
                    "device_ips": ["192.168.1.100", "192.168.1.101"],
                    "component_type": "switch",
                    "config": {"in_mode": "button"},
                },
            )

            assert response.status_code == 201
            data = response.json()

            assert len(data) == 2
            assert data[0]["success"] is True
            assert data[1]["success"] is False
            assert data[1]["error"] == "Device unreachable"

    def test_it_validates_bulk_apply_config_errors(self):

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

        with create_test_client(
            route_handlers=[bulk_apply_config],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            # Test missing device_ips
            response = client.post(
                "/bulk/apply-config",
                json={"component_type": "switch", "config": {"in_mode": "button"}},
            )
            assert response.status_code == 400

            # Test missing component_type
            response = client.post(
                "/bulk/apply-config",
                json={"device_ips": ["192.168.1.100"], "config": {"in_mode": "button"}},
            )
            assert response.status_code == 400

            # Test missing config
            response = client.post(
                "/bulk/apply-config",
                json={"device_ips": ["192.168.1.100"], "component_type": "switch"},
            )
            assert response.status_code == 400

            # Test empty device_ips
            response = client.post(
                "/bulk/apply-config",
                json={
                    "device_ips": [],
                    "component_type": "switch",
                    "config": {"in_mode": "button"},
                },
            )
            assert response.status_code == 400

            # Test empty config
            response = client.post(
                "/bulk/apply-config",
                json={
                    "device_ips": ["192.168.1.100"],
                    "component_type": "switch",
                    "config": {},
                },
            )
            assert response.status_code == 400

            # Test invalid IP address
            response = client.post(
                "/bulk/apply-config",
                json={
                    "device_ips": ["invalid-ip"],
                    "component_type": "switch",
                    "config": {"in_mode": "button"},
                },
            )
            assert response.status_code == 400

            # Test invalid component type
            response = client.post(
                "/bulk/apply-config",
                json={
                    "device_ips": ["192.168.1.100"],
                    "component_type": "invalid_component",
                    "config": {"in_mode": "button"},
                },
            )
            assert response.status_code == 400

    def test_it_handles_bulk_config_internal_server_errors(self):

        class MockBulkOperationsUseCase(BulkOperationsUseCase):
            def __init__(self):
                pass

            async def export_bulk_config(self, device_ips, component_types):
                raise Exception("Internal error")

            async def apply_bulk_config(self, device_ips, component_type, config):
                raise Exception("Internal error")

        with create_test_client(
            route_handlers=[bulk_export_config, bulk_apply_config],
            dependencies={
                "bulk_operations_use_case": Provide(
                    lambda: MockBulkOperationsUseCase(), sync_to_thread=False
                )
            },
        ) as client:
            # Test export error
            response = client.post(
                "/bulk/export-config",
                json={"device_ips": ["192.168.1.100"], "component_types": ["switch"]},
            )
            assert response.status_code == 500
            # Response might be text or JSON, so check both
            try:
                detail = response.json()["detail"]
            except Exception:
                detail = response.text
            assert "Internal error" in detail

            # Test apply error
            response = client.post(
                "/bulk/apply-config",
                json={
                    "device_ips": ["192.168.1.100"],
                    "component_type": "switch",
                    "config": {"in_mode": "button"},
                },
            )
            assert response.status_code == 500
            # Response might be text or JSON, so check both
            try:
                detail = response.json()["detail"]
            except Exception:
                detail = response.text
            assert "Internal error" in detail
