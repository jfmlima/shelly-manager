"""
Device management API routes using core interactors.
"""

from typing import TypeVar

from core.domain.value_objects.check_device_status_request import (
    CheckDeviceStatusRequest,
)
from core.domain.value_objects.component_action_request import ComponentActionRequest
from core.domain.value_objects.get_component_actions_request import (
    GetComponentActionsRequest,
)
from core.domain.value_objects.scan_request import ScanRequest
from core.use_cases.bulk_operations import BulkOperationsUseCase
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.execute_component_action import ExecuteComponentActionUseCase
from core.use_cases.get_component_actions import GetComponentActionsUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from litestar import Router, get, post
from litestar.exceptions import HTTPException
from litestar.params import Body

from ..presentation.dto.requests import BulkApplyConfigRequest, BulkExportConfigRequest
from ..presentation.dto.responses import (
    BulkApplyConfigResponse,
    BulkExportConfigResponse,
)
from ..presentation.exceptions import DeviceNotFoundHTTPException

T = TypeVar("T")


def _require(dep_name: str, dep: T | None) -> T:
    if dep is None:
        raise HTTPException(status_code=500, detail=f"Missing dependency: {dep_name}")
    return dep


@get("/scan", tags=["Devices"], summary="Scan Network for Devices")
async def scan_devices(
    targets: list[str] | None = None,
    use_predefined: bool = True,
    use_mdns: bool = False,
    max_workers: int = 50,
    timeout: float = 3.0,
    scan_interactor: ScanDevicesUseCase | None = None,
) -> list[dict]:
    """
    Discover Shelly devices on the network.

    Scans the specified IP range or predefined ranges to find Shelly devices.
    Returns device information including IP, status, type, and firmware version.

    Args:
        targets: List of IP targets (IPs, ranges, or CIDR)
        use_predefined: Whether to use predefined IP ranges from config
        use_mdns: Whether to use mDNS to discover devices
        max_workers: Maximum concurrent workers for scanning
        timeout: Connection timeout per device (seconds) or mDNS scan duration

    Returns:
        list[dict]: List of discovered devices with their information
    """
    scan_interactor = _require("scan_interactor", scan_interactor)

    scan_request = ScanRequest(
        targets=targets or [],
        use_predefined=use_predefined,
        use_mdns=use_mdns,
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


@get(
    "/{ip:str}/components/actions",
    tags=["Components"],
    summary="Discover Device Component Actions",
)
async def get_component_actions(
    ip: str,
    component_actions_interactor: GetComponentActionsUseCase | None = None,
) -> dict:
    """
    Discover available actions for all device components.

    Retrieves component information and supported actions for a specific Shelly device.
    Each device component (switches, covers, lights, sensors) has different available actions.

    Args:
        ip: The device's IP address (e.g., "192.168.1.100")

    Returns:
        dict: Component information with available actions for each component
    """
    component_actions_interactor = _require(
        "component_actions_interactor", component_actions_interactor
    )

    request = GetComponentActionsRequest(device_ip=ip)
    actions = await component_actions_interactor.execute(request)

    return {"ip": ip, "component_actions": actions}


@post(
    "/{ip:str}/components/{component_key:str}/actions/{action:str}",
    status_code=200,
    tags=["Components"],
    summary="Control Device Components",
)
async def execute_component_action(
    ip: str,
    component_key: str,
    action: str,
    data: dict = Body(),
    execute_component_action_interactor: ExecuteComponentActionUseCase | None = None,
) -> dict:
    """
    Execute an action on a specific device component.

    Performs the specified action on a device component such as turning on a switch,
    opening a cover, or adjusting light brightness. Parameters can be provided in the
    request body for actions that require additional configuration.

    Args:
        ip: Device IP address (e.g., "192.168.1.100")
        component_key: Component identifier (e.g., "switch:0", "cover:0")
        action: Action to execute (e.g., "turn_on", "toggle", "open", "close")
        data: Additional parameters for the action

    Returns:
        dict: Action execution result and updated component state
    """
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


@get("/{ip:str}/status", tags=["Devices"], summary="Get Device Status")
async def get_device_status(
    ip: str,
    include_updates: bool = True,
    status_interactor: CheckDeviceStatusUseCase | None = None,
) -> dict:
    """
    Retrieve comprehensive status information for a specific device.

    Returns detailed information about the device including component states,
    system information, firmware details, and available updates.

    Args:
        ip: Device IP address (e.g., "192.168.1.100")
        include_updates: Whether to include firmware update information

    Returns:
        dict: Complete device status including components and system information
    """
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
        raise DeviceNotFoundHTTPException(ip)


@post(
    "/{ip:str}/update",
    status_code=200,
    tags=["Devices"],
    summary="Update Device Firmware",
)
async def update_device(
    ip: str,
    data: dict = Body(),
    execute_component_action_interactor: ExecuteComponentActionUseCase | None = None,
) -> dict:
    """
    Initiate firmware update for a device.

    Updates the device firmware to the latest version from the specified channel.
    The device will download and install the update, which may take several minutes.

    Args:
        ip: Device IP address (e.g., "192.168.1.100")
        data: Update parameters with optional "channel" field (stable/beta)

    Returns:
        dict: Update operation result and status
    """
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


@post("/{ip:str}/reboot", status_code=200, tags=["Devices"], summary="Reboot Device")
async def reboot_device(
    ip: str,
    execute_component_action_interactor: ExecuteComponentActionUseCase | None = None,
) -> dict:
    """
    Restart a device.

    Performs a soft restart of the device. The device will be temporarily unavailable
    during the reboot process, typically for 10-30 seconds.

    Args:
        ip: Device IP address (e.g., "192.168.1.100")

    Returns:
        dict: Reboot operation result and status
    """
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


@post("/bulk", status_code=200, tags=["Devices"], summary="Execute Bulk Operations")
async def execute_bulk_operations(
    data: dict = Body(),
    bulk_operations_use_case: BulkOperationsUseCase | None = None,
) -> list[dict]:
    """
    Execute operations on multiple devices simultaneously.

    Performs the specified operation on a list of devices. Supported operations
    include firmware updates, device reboots, and factory resets. Results are
    returned for each device individually.

    Args:
        data: Request containing device_ips list and operation type

    Returns:
        list[dict]: Operation results for each device with success status
    """

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


@post("/bulk/config/export")
async def bulk_export_config(
    data: BulkExportConfigRequest,
    bulk_operations_use_case: BulkOperationsUseCase | None = None,
) -> BulkExportConfigResponse:
    """Export component configurations from multiple devices."""
    bulk_operations_use_case = _require(
        "bulk_operations_use_case", bulk_operations_use_case
    )

    try:
        result = await bulk_operations_use_case.export_bulk_config(
            data.device_ips, data.component_types
        )
        return BulkExportConfigResponse(
            export_metadata=result["export_metadata"], devices=result["devices"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@post("/bulk/config/apply")
async def bulk_apply_config(
    data: BulkApplyConfigRequest,
    bulk_operations_use_case: BulkOperationsUseCase | None = None,
) -> list[BulkApplyConfigResponse]:
    """Apply component configuration to multiple devices."""
    bulk_operations_use_case = _require(
        "bulk_operations_use_case", bulk_operations_use_case
    )

    try:
        results = await bulk_operations_use_case.apply_bulk_config(
            data.device_ips, data.component_type, data.config
        )
        return [
            BulkApplyConfigResponse(
                ip=result.device_ip,
                component_key=(
                    result.action_type.split(".")[0]
                    if "." in result.action_type
                    else ""
                ),
                success=result.success,
                message=result.message,
                error=result.error,
            )
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
        update_device,
        reboot_device,
        execute_bulk_operations,
        bulk_export_config,
        bulk_apply_config,
    ],
)
