"""Controller for device configuration backups."""

from core.domain.entities.device_backup import DeviceBackup, DeviceBackupSummary
from core.domain.entities.exceptions import DeviceNotFoundError
from core.use_cases.backup_device_config import (
    BackupDeviceConfig,
    BackupError,
    BackupNotFoundError,
)
from core.use_cases.restore_device_config import (
    DeviceMismatchError,
    RestoreDeviceConfig,
)
from litestar import Controller, Router, delete, get, post
from litestar.exceptions import HTTPException, NotFoundException

from api.presentation.dto.requests import CreateBackupRequest, RestoreBackupRequest
from api.presentation.dto.responses import (
    BackupDetailResponse,
    BackupSummaryResponse,
    ComponentRestoreResultResponse,
    RestoreResultResponse,
)
from api.presentation.exceptions import DeviceNotFoundHTTPException


class BackupsController(Controller):
    path = ""
    tags = ["Backups"]

    @get()
    async def list_backups(
        self,
        backup_use_case: BackupDeviceConfig,
        device_mac: str | None = None,
    ) -> list[BackupSummaryResponse]:
        """List stored backups, newest first, optionally filtered by device MAC."""
        summaries = await backup_use_case.list_backups(device_mac)
        return [_to_summary(s) for s in summaries]

    @post()
    async def create_backup(
        self,
        data: CreateBackupRequest,
        backup_use_case: BackupDeviceConfig,
    ) -> BackupDetailResponse:
        """Capture a full configuration backup of a device."""
        try:
            backup = await backup_use_case.create_backup(
                device_ip=data.device_ip, name=data.name
            )
        except DeviceNotFoundError as err:
            raise DeviceNotFoundHTTPException(data.device_ip) from err
        except BackupError as err:
            raise HTTPException(status_code=422, detail=str(err)) from err
        return _to_detail(backup)

    @get("/{backup_id:int}")
    async def get_backup(
        self,
        backup_id: int,
        backup_use_case: BackupDeviceConfig,
    ) -> BackupDetailResponse:
        """Get a backup including its full snapshot."""
        try:
            backup = await backup_use_case.get_backup(backup_id)
        except BackupNotFoundError as err:
            raise NotFoundException(detail=f"Backup not found: {backup_id}") from err
        return _to_detail(backup)

    @post("/{backup_id:int}/restore")
    async def restore_backup(
        self,
        backup_id: int,
        data: RestoreBackupRequest,
        restore_use_case: RestoreDeviceConfig,
    ) -> RestoreResultResponse:
        """Restore selected components from a backup onto a device."""
        try:
            result = await restore_use_case.restore(
                backup_id,
                data.device_ip,
                component_keys=data.component_keys,
                allow_mac_mismatch=data.allow_mac_mismatch,
                reboot=data.reboot,
            )
        except BackupNotFoundError as err:
            raise NotFoundException(detail=f"Backup not found: {backup_id}") from err
        except DeviceNotFoundError as err:
            raise DeviceNotFoundHTTPException(data.device_ip) from err
        except DeviceMismatchError as err:
            raise HTTPException(status_code=409, detail=str(err)) from err

        return RestoreResultResponse(
            success=result.success,
            device_ip=result.device_ip,
            backup_id=result.backup_id,
            total=result.total,
            succeeded=result.succeeded,
            failed=result.failed,
            skipped=result.skipped,
            message=result.message,
            components=[
                ComponentRestoreResultResponse(
                    key=c.key,
                    action=c.action,
                    success=c.success,
                    skipped=c.skipped,
                    skipped_reason=c.skipped_reason,
                    error=c.error,
                )
                for c in result.components
            ],
        )

    @delete("/{backup_id:int}")
    async def delete_backup(
        self,
        backup_id: int,
        backup_use_case: BackupDeviceConfig,
    ) -> None:
        """Delete a backup."""
        try:
            await backup_use_case.delete_backup(backup_id)
        except BackupNotFoundError as err:
            raise NotFoundException(detail=f"Backup not found: {backup_id}") from err


backups_router = Router(
    path="/backups",
    route_handlers=[BackupsController],
)


def _to_summary(summary: DeviceBackupSummary) -> BackupSummaryResponse:
    return BackupSummaryResponse(
        id=summary.id or 0,
        device_mac=summary.device_mac,
        device_ip=summary.device_ip,
        device_name=summary.device_name,
        device_type=summary.device_type,
        firmware_version=summary.firmware_version,
        generation=summary.generation,
        name=summary.name,
        source=summary.source,
        sha256=summary.sha256,
        size_bytes=summary.size_bytes,
        created_at=summary.created_at,
    )


def _to_detail(backup: DeviceBackup) -> BackupDetailResponse:
    return BackupDetailResponse(
        id=backup.id or 0,
        device_mac=backup.device_mac,
        device_ip=backup.device_ip,
        device_name=backup.device_name,
        device_type=backup.device_type,
        firmware_version=backup.firmware_version,
        generation=backup.generation,
        name=backup.name,
        source=backup.source,
        sha256=backup.sha256,
        size_bytes=backup.size_bytes,
        created_at=backup.created_at,
        snapshot=backup.snapshot,
    )
