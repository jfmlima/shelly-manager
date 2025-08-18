"""
Device management API routes using core interactors.
"""

from typing import TypeVar

from core.domain.enums.enums import UpdateChannel
from core.domain.value_objects.bulk_update_device_firmware_request import (
    BulkUpdateDeviceFirmwareRequest,
)
from core.domain.value_objects.check_device_status_request import (
    CheckDeviceStatusRequest,
)
from core.domain.value_objects.device_configuration_request import (
    DeviceConfigurationRequest,
)
from core.domain.value_objects.reboot_device_request import RebootDeviceRequest
from core.domain.value_objects.scan_request import ScanRequest
from core.domain.value_objects.set_configuration_request import SetConfigurationRequest
from core.domain.value_objects.update_device_firmware_request import (
    UpdateDeviceFirmwareRequest,
)
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.reboot_device import RebootDeviceUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase
from litestar import Router, get, post
from litestar.exceptions import HTTPException
from litestar.params import Body

T = TypeVar("T")


def _require(dep_name: str, dep: T | None) -> T:
    if dep is None:
        raise HTTPException(status_code=500, detail=f"Missing dependency: {dep_name}")
    return dep


@get("/scan")  # type: ignore[misc]
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


@post("/{ip:str}/update", status_code=200)  # type: ignore[misc]
async def update_device(
    ip: str,
    channel: str = "stable",
    update_interactor: UpdateDeviceFirmwareUseCase | None = None,
) -> dict:
    update_interactor = _require("update_interactor", update_interactor)

    update_channel = (
        UpdateChannel.STABLE if channel.lower() == "stable" else UpdateChannel.BETA
    )
    request = UpdateDeviceFirmwareRequest(device_ip=ip, channel=update_channel)
    result = await update_interactor.execute(request)

    return {
        "ip": result.device_ip,
        "success": result.success,
        "message": result.message,
        "error": result.error,
        "action_type": result.action_type,
    }


@post("/bulk/update")  # type: ignore[misc]
async def bulk_update_devices(
    data: dict = Body(), update_interactor: UpdateDeviceFirmwareUseCase | None = None
) -> list[dict]:
    update_interactor = _require("update_interactor", update_interactor)

    device_ips = data.get("device_ips", [])
    channel = data.get("channel", "stable")

    update_channel = (
        UpdateChannel.STABLE if channel.lower() == "stable" else UpdateChannel.BETA
    )
    request = BulkUpdateDeviceFirmwareRequest(
        device_ips=device_ips, channel=update_channel
    )
    results = await update_interactor.execute_bulk(request)

    return [
        {
            "ip": result.device_ip,
            "success": result.success,
            "message": result.message,
            "error": result.error,
            "action_type": result.action_type,
        }
        for result in results
    ]


@post("/{ip:str}/reboot", status_code=200)  # type: ignore[misc]
async def reboot_device(
    ip: str, reboot_interactor: RebootDeviceUseCase | None = None
) -> dict:
    reboot_interactor = _require("reboot_interactor", reboot_interactor)

    request = RebootDeviceRequest(device_ip=ip)
    result = await reboot_interactor.execute(request)

    return {
        "ip": result.device_ip,
        "success": result.success,
        "message": result.message,
        "error": result.error,
        "action_type": result.action_type,
    }


@get("/{ip:str}/status")  # type: ignore[misc]
async def get_device_status(
    ip: str,
    include_updates: bool = True,
    status_interactor: CheckDeviceStatusUseCase | None = None,
) -> dict:
    status_interactor = _require("status_interactor", status_interactor)

    request = CheckDeviceStatusRequest(device_ip=ip, include_updates=include_updates)
    device_status = await status_interactor.execute(request)
    if device_status:
        # Return component-based response
        summary = device_status.get_device_summary()
        system_info = device_status.get_system_info()

        # Extract firmware information
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
                }
                for comp in device_status.components
            ],
            "summary": summary,
            "firmware": firmware_info,
            "last_updated": device_status.last_updated.isoformat(),
            "total_components": device_status.total_components,
        }
    else:
        return {"ip": ip, "error": "Device not found or unreachable"}


@get("/{ip:str}/config")  # type: ignore[misc]
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


@post("/{ip:str}/config", status_code=200)  # type: ignore[misc]
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


devices_router = Router(
    path="/devices",
    route_handlers=[
        scan_devices,
        update_device,
        bulk_update_devices,
        reboot_device,
        get_device_status,
        get_device_config,
        set_device_config,
    ],
)
