"""
Device management API routes using core interactors.
"""

from core.domain.enums.enums import UpdateChannel
from core.domain.value_objects.scan_request import ScanRequest
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.reboot_device import RebootDeviceUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase
from litestar import Router, get, post
from litestar.params import Body


@get("/scan")
async def scan_devices(
    start_ip: str | None = None,
    end_ip: str | None = None,
    use_predefined: bool = True,
    timeout: float = 3.0,
    max_workers: int = 50,
    scan_interactor: ScanDevicesUseCase | None = None,
) -> list[dict]:
    assert scan_interactor is not None

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


@post("/{ip:str}/update", status_code=200)
async def update_device(
    ip: str,
    channel: str = "stable",
    update_interactor: UpdateDeviceFirmwareUseCase | None = None,
) -> dict:
    assert update_interactor is not None

    update_channel = (
        UpdateChannel.STABLE if channel.lower() == "stable" else UpdateChannel.BETA
    )
    result = await update_interactor.execute(ip, update_channel)

    return {
        "ip": result.device_ip,
        "success": result.success,
        "message": result.message,
        "error": result.error,
        "action_type": result.action_type,
    }


@post("/bulk/update")
async def bulk_update_devices(
    data: dict = Body(), update_interactor: UpdateDeviceFirmwareUseCase | None = None
) -> list[dict]:
    assert update_interactor is not None

    device_ips = data.get("device_ips", [])
    channel = data.get("channel", "stable")

    update_channel = (
        UpdateChannel.STABLE if channel.lower() == "stable" else UpdateChannel.BETA
    )
    results = await update_interactor.execute_bulk(device_ips, update_channel)

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


@post("/{ip:str}/reboot", status_code=200)
async def reboot_device(
    ip: str, reboot_interactor: RebootDeviceUseCase | None = None
) -> dict:
    assert reboot_interactor is not None

    result = await reboot_interactor.execute(ip)

    return {
        "ip": result.device_ip,
        "success": result.success,
        "message": result.message,
        "error": result.error,
        "action_type": result.action_type,
    }


@get("/{ip:str}/status")
async def get_device_status(
    ip: str,
    include_updates: bool = True,
    status_interactor: CheckDeviceStatusUseCase | None = None,
) -> dict:
    assert status_interactor is not None

    device = await status_interactor.execute(ip, include_updates)

    if device:
        return {
            "ip": device.ip,
            "status": device.status,
            "device_type": device.device_type,
            "device_name": device.device_name,
            "firmware_version": device.firmware_version,
            "response_time": device.response_time,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }
    else:
        return {"ip": ip, "error": "Device not found or unreachable"}


@get("/{ip:str}/config")
async def get_device_config(
    ip: str, get_config_interactor: GetConfigurationUseCase | None = None
) -> dict:
    assert get_config_interactor is not None

    try:
        config = await get_config_interactor.execute(ip)
        return {"ip": ip, "success": True, "config": config}
    except Exception as e:
        return {"ip": ip, "success": False, "error": str(e)}


@post("/{ip:str}/config", status_code=200)
async def set_device_config(
    ip: str,
    data: dict = Body(),
    set_config_interactor: SetConfigurationUseCase | None = None,
) -> dict:
    assert set_config_interactor is not None

    try:
        config = data.get("config", {})
        result = await set_config_interactor.execute(ip, config)
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
