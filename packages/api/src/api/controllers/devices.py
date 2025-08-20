"""
Device management API routes using core interactors.
"""

from typing import TypeVar

from core.domain.value_objects.check_device_status_request import (
    CheckDeviceStatusRequest,
)
from core.domain.value_objects.component_action_request import ComponentActionRequest
from core.domain.value_objects.device_configuration_request import (
    DeviceConfigurationRequest,
)
from core.domain.value_objects.get_component_actions_request import (
    GetComponentActionsRequest,
)
from core.domain.value_objects.scan_request import ScanRequest
from core.domain.value_objects.set_configuration_request import SetConfigurationRequest
from core.use_cases.bulk_operations import BulkOperationsUseCase
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.execute_component_action import ExecuteComponentActionUseCase
from core.use_cases.get_component_actions import GetComponentActionsUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
from litestar import Router, get, post
from litestar.exceptions import HTTPException
from litestar.params import Body

T = TypeVar("T")


def _require(dep_name: str, dep: T | None) -> T:
    if dep is None:
        raise HTTPException(status_code=500, detail=f"Missing dependency: {dep_name}")
    return dep


@get("/scan")
async def scan_devices(
    start_ip: str | None = None,
    end_ip: str | None = None,
    use_predefined: bool = True,
    timeout: float = 3.0,
    max_workers: int = 50,
    scan_interactor: ScanDevicesUseCase | None = None,
) -> list[dict]:
    scan_interactor = _require("scan_interactor", scan_interactor)

    scan_request = ScanRequest(
        start_ip=start_ip,
        end_ip=end_ip,
        use_predefined=use_predefined,
        timeout=timeout,
        max_workers=max_workers,
    )

    devices = await scan_interactor.execute(scan_request)

    return [
        {
            "ip": device.ip,
            "status": device.status,
            "device_type": device.device_type,
            "device_name": device.device_name,
            "firmware_version": device.firmware_version,
            "response_time": device.response_time,
            "error_message": device.error_message,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }
        for device in devices
    ]


@get("/{ip:str}/components/actions")
async def get_component_actions(
    ip: str,
    component_actions_interactor: GetComponentActionsUseCase | None = None,
) -> dict:
    """Get available actions for all device components."""
    component_actions_interactor = _require(
        "component_actions_interactor", component_actions_interactor
    )

    request = GetComponentActionsRequest(device_ip=ip)
    actions = await component_actions_interactor.execute(request)

    return {"ip": ip, "component_actions": actions}


@post("/{ip:str}/components/{component_key:str}/actions/{action:str}", status_code=200)
async def execute_component_action(
    ip: str,
    component_key: str,
    action: str,
    data: dict = Body(),
    execute_component_action_interactor: ExecuteComponentActionUseCase | None = None,
) -> dict:
    """Execute action on device component."""
    execute_component_action_interactor = _require(
        "execute_component_action_interactor", execute_component_action_interactor
    )

    request = ComponentActionRequest(
        device_ip=ip,
        component_key=component_key,
        action=action,
        parameters=data,
    )

    result = await execute_component_action_interactor.execute(request)

    return {
        "ip": result.device_ip,
        "component_key": component_key,
        "action": action,
        "success": result.success,
        "message": result.message,
        "error": result.error,
        "data": result.data,
        "action_type": result.action_type,
    }


@get("/{ip:str}/status")
async def get_device_status(
    ip: str,
    include_updates: bool = True,
    status_interactor: CheckDeviceStatusUseCase | None = None,
) -> dict:
    status_interactor = _require("status_interactor", status_interactor)

    request = CheckDeviceStatusRequest(device_ip=ip, include_updates=include_updates)
    device_status = await status_interactor.execute(request)
    if device_status:
        summary = device_status.get_device_summary()
        system_info = device_status.get_system_info()

        firmware_info = {}
        if system_info:
            firmware_info = {
                "current_version": system_info.firmware_version,
                "available_updates": system_info.available_updates,
                "restart_required": system_info.restart_required,
            }

        return {
            "ip": device_status.device_ip,
            "components": [
                {
                    "key": comp.key,
                    "type": comp.component_type,
                    "id": comp.component_id,
                    "status": comp.status,
                    "config": comp.config,
                    "available_actions": comp.available_actions,
                }
                for comp in device_status.components
            ],
            "available_methods": device_status.available_methods,
            "summary": summary,
            "firmware": firmware_info,
            "last_updated": device_status.last_updated.isoformat(),
            "total_components": device_status.total_components,
        }
    else:
        return {"ip": ip, "error": "Device not found or unreachable"}


@get("/{ip:str}/config")
async def get_device_config(
    ip: str, get_config_interactor: GetConfigurationUseCase | None = None
) -> dict:
    get_config_interactor = _require("get_config_interactor", get_config_interactor)

    try:
        request = DeviceConfigurationRequest(device_ip=ip)
        config = await get_config_interactor.execute(request)
        return {"ip": ip, "success": True, "config": config}
    except Exception as e:
        return {"ip": ip, "success": False, "error": str(e)}


@post("/{ip:str}/config", status_code=200)
async def set_device_config(
    ip: str,
    data: dict = Body(),
    set_config_interactor: SetConfigurationUseCase | None = None,
) -> dict:
    set_config_interactor = _require("set_config_interactor", set_config_interactor)

    try:
        config = data.get("config", {})
        request = SetConfigurationRequest(device_ip=ip, config=config)
        result = await set_config_interactor.execute(request)
        return {
            "ip": ip,
            "success": result["success"],
            "message": result["message"],
        }
    except Exception as e:
        return {"ip": ip, "success": False, "error": str(e)}


@post("/{ip:str}/update", status_code=200)
async def update_device(
    ip: str,
    data: dict = Body(),
    execute_component_action_interactor: ExecuteComponentActionUseCase | None = None,
) -> dict:
    """Convenience endpoint for firmware updates (shortcut for component action)."""
    execute_component_action_interactor = _require(
        "execute_component_action_interactor", execute_component_action_interactor
    )

    channel = data.get("channel", "stable")
    parameters = {"channel": channel} if channel != "stable" else {}

    request = ComponentActionRequest(
        device_ip=ip,
        component_key="shelly",
        action="Update",
        parameters=parameters,
    )

    result = await execute_component_action_interactor.execute(request)

    return {
        "ip": result.device_ip,
        "success": result.success,
        "message": result.message,
        "error": result.error,
        "action_type": result.action_type,
        "channel": channel,
    }


@post("/{ip:str}/reboot", status_code=200)
async def reboot_device(
    ip: str,
    execute_component_action_interactor: ExecuteComponentActionUseCase | None = None,
) -> dict:
    """Convenience endpoint for device reboot (shortcut for component action)."""
    execute_component_action_interactor = _require(
        "execute_component_action_interactor", execute_component_action_interactor
    )

    request = ComponentActionRequest(
        device_ip=ip,
        component_key="shelly",
        action="Reboot",
        parameters={},
    )

    result = await execute_component_action_interactor.execute(request)

    return {
        "ip": result.device_ip,
        "success": result.success,
        "message": result.message,
        "error": result.error,
        "action_type": result.action_type,
    }


@post("/bulk", status_code=200)
async def execute_bulk_operations(
    data: dict = Body(),
    bulk_operations_use_case: BulkOperationsUseCase | None = None,
) -> list[dict]:
    """Unified bulk operations endpoint."""

    bulk_operations_use_case = _require(
        "bulk_operations_use_case", bulk_operations_use_case
    )

    device_ips = data.get("device_ips", [])
    operation = data.get("operation")

    if not device_ips:
        raise HTTPException(status_code=400, detail="device_ips is required")

    if not operation:
        raise HTTPException(status_code=400, detail="operation is required")

    if operation not in ["update", "reboot", "factory_reset"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported operation: {operation}. Supported: update, reboot, factory_reset",
        )

    try:
        if operation == "update":
            channel = data.get("channel", "stable")
            results = await bulk_operations_use_case.execute_bulk_update(
                device_ips, channel
            )
        elif operation == "reboot":
            results = await bulk_operations_use_case.execute_bulk_reboot(device_ips)
        elif operation == "factory_reset":
            results = await bulk_operations_use_case.execute_bulk_factory_reset(
                device_ips
            )

        parameters = {
            k: v for k, v in data.items() if k not in ["device_ips", "operation"]
        }

        return [
            {
                "ip": result.device_ip,
                "success": result.success,
                "message": result.message,
                "error": result.error,
                "action_type": result.action_type,
                "operation": operation,
                **parameters,
            }
            for result in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


devices_router = Router(
    path="/devices",
    route_handlers=[
        scan_devices,
        get_component_actions,
        execute_component_action,
        get_device_status,
        get_device_config,
        set_device_config,
        update_device,
        reboot_device,
        execute_bulk_operations,
    ],
)
