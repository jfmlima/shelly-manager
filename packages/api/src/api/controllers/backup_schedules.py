"""Controller for automated backup schedules."""

from core.domain.entities.backup_schedule import BackupSchedule
from core.use_cases.manage_backup_schedules import ManageBackupSchedulesUseCase
from core.use_cases.run_due_backups import RunDueBackupsUseCase
from litestar import Controller, Router, delete, get, post, put

from api.presentation.dto.requests import (
    CreateBackupScheduleRequest,
    UpdateBackupScheduleRequest,
)
from api.presentation.dto.responses import (
    BackupScheduleResponse,
    ScheduleRunResultResponse,
)


class BackupSchedulesController(Controller):
    path = ""
    tags = ["Backup Schedules"]

    @get()
    async def list_schedules(
        self,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> list[BackupScheduleResponse]:
        """List all backup schedules, newest first."""
        schedules = await manage_schedules_use_case.list_schedules()
        return [_to_response(s) for s in schedules]

    @post()
    async def create_schedule(
        self,
        data: CreateBackupScheduleRequest,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> BackupScheduleResponse:
        """Create a new backup schedule."""
        schedule = BackupSchedule(
            name=data.name,
            interval_seconds=data.resolved_interval_seconds(),
            target_ips=data.target_ips,
            target_macs=data.target_macs,
            all_credentialed=data.all_credentialed,
            enabled=data.enabled,
            retention_keep_last=data.retention_keep_last,
            retention_max_age_days=data.retention_max_age_days,
        )
        created = await manage_schedules_use_case.create_schedule(schedule)
        return _to_response(created)

    @get("/{schedule_id:int}")
    async def get_schedule(
        self,
        schedule_id: int,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> BackupScheduleResponse:
        """Get a backup schedule by ID."""
        schedule = await manage_schedules_use_case.get_schedule(schedule_id)
        return _to_response(schedule)

    @put("/{schedule_id:int}")
    async def update_schedule(
        self,
        schedule_id: int,
        data: UpdateBackupScheduleRequest,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> BackupScheduleResponse:
        """Partially update a backup schedule."""
        result = await manage_schedules_use_case.apply_schedule_update(
            schedule_id,
            name=data.name,
            interval_seconds=data.resolved_interval_seconds(),
            target_ips=data.target_ips,
            target_macs=data.target_macs,
            all_credentialed=data.all_credentialed,
            enabled=data.enabled,
            retention_keep_last=data.retention_keep_last,
            retention_max_age_days=data.retention_max_age_days,
        )
        return _to_response(result)

    @delete("/{schedule_id:int}")
    async def delete_schedule(
        self,
        schedule_id: int,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> None:
        """Delete a backup schedule."""
        await manage_schedules_use_case.delete_schedule(schedule_id)

    @post("/{schedule_id:int}/enable")
    async def enable_schedule(
        self,
        schedule_id: int,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> BackupScheduleResponse:
        """Enable a backup schedule."""
        return await self._set_enabled(manage_schedules_use_case, schedule_id, True)

    @post("/{schedule_id:int}/disable")
    async def disable_schedule(
        self,
        schedule_id: int,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> BackupScheduleResponse:
        """Disable a backup schedule."""
        return await self._set_enabled(manage_schedules_use_case, schedule_id, False)

    @post("/{schedule_id:int}/run")
    async def run_schedule(
        self,
        schedule_id: int,
        run_due_backups_use_case: RunDueBackupsUseCase,
    ) -> ScheduleRunResultResponse:
        """Run a backup schedule now, ignoring its next run time."""
        result = await run_due_backups_use_case.run_schedule(schedule_id)
        return ScheduleRunResultResponse(
            schedule_id=result.schedule_id,
            schedule_name=result.schedule_name,
            status=result.status,
            targets=result.targets,
            ok=result.ok,
            failed=result.failed,
            skipped=result.skipped,
            message=result.message,
        )

    @staticmethod
    async def _set_enabled(
        use_case: ManageBackupSchedulesUseCase,
        schedule_id: int,
        enabled: bool,
    ) -> BackupScheduleResponse:
        updated = await use_case.set_enabled(schedule_id, enabled)
        return _to_response(updated)


backup_schedules_router = Router(
    path="/backup-schedules",
    route_handlers=[BackupSchedulesController],
)


def _to_response(schedule: BackupSchedule) -> BackupScheduleResponse:
    return BackupScheduleResponse(
        id=schedule.id or 0,
        name=schedule.name,
        target_ips=schedule.target_ips,
        target_macs=schedule.target_macs,
        all_credentialed=schedule.all_credentialed,
        interval_seconds=schedule.interval_seconds,
        enabled=schedule.enabled,
        retention_keep_last=schedule.retention_keep_last,
        retention_max_age_days=schedule.retention_max_age_days,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        last_status=schedule.last_status,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )
