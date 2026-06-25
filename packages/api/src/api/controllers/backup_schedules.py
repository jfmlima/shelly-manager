"""Controller for automated backup schedules."""

from core.domain.entities.backup_schedule import BackupSchedule
from core.use_cases.manage_backup_schedules import (
    ManageBackupSchedulesUseCase,
    ScheduleAlreadyExistsError,
    ScheduleNotFoundError,
)
from core.use_cases.run_due_backups import RunDueBackupsUseCase
from litestar import Controller, Router, delete, get, post, put
from litestar.exceptions import HTTPException, NotFoundException
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT

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
        try:
            created = await manage_schedules_use_case.create_schedule(schedule)
        except ScheduleAlreadyExistsError as err:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"Schedule already exists: {data.name}",
            ) from err
        return _to_response(created)

    @get("/{schedule_id:int}")
    async def get_schedule(
        self,
        schedule_id: int,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> BackupScheduleResponse:
        """Get a backup schedule by ID."""
        try:
            schedule = await manage_schedules_use_case.get_schedule(schedule_id)
        except ScheduleNotFoundError as err:
            raise NotFoundException(
                detail=f"Schedule not found: {schedule_id}"
            ) from err
        return _to_response(schedule)

    @put("/{schedule_id:int}")
    async def update_schedule(
        self,
        schedule_id: int,
        data: UpdateBackupScheduleRequest,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> BackupScheduleResponse:
        """Partially update a backup schedule."""
        try:
            existing = await manage_schedules_use_case.get_schedule(schedule_id)
        except ScheduleNotFoundError as err:
            raise NotFoundException(
                detail=f"Schedule not found: {schedule_id}"
            ) from err

        interval = data.resolved_interval_seconds()
        updated = BackupSchedule(
            id=schedule_id,
            name=data.name if data.name is not None else existing.name,
            interval_seconds=(
                interval if interval is not None else existing.interval_seconds
            ),
            target_ips=(
                data.target_ips if data.target_ips is not None else existing.target_ips
            ),
            target_macs=(
                data.target_macs
                if data.target_macs is not None
                else existing.target_macs
            ),
            all_credentialed=(
                data.all_credentialed
                if data.all_credentialed is not None
                else existing.all_credentialed
            ),
            enabled=data.enabled if data.enabled is not None else existing.enabled,
            retention_keep_last=(
                data.retention_keep_last
                if data.retention_keep_last is not None
                else existing.retention_keep_last
            ),
            retention_max_age_days=(
                data.retention_max_age_days
                if data.retention_max_age_days is not None
                else existing.retention_max_age_days
            ),
            next_run_at=existing.next_run_at,
        )
        if not (updated.target_ips or updated.target_macs or updated.all_credentialed):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=(
                    "A schedule needs at least one target "
                    "(target_ips, target_macs, or all_credentialed)"
                ),
            )
        try:
            result = await manage_schedules_use_case.update_schedule(updated)
        except ScheduleAlreadyExistsError as err:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"Schedule name already exists: {data.name}",
            ) from err
        return _to_response(result)

    @delete("/{schedule_id:int}")
    async def delete_schedule(
        self,
        schedule_id: int,
        manage_schedules_use_case: ManageBackupSchedulesUseCase,
    ) -> None:
        """Delete a backup schedule."""
        try:
            await manage_schedules_use_case.delete_schedule(schedule_id)
        except ScheduleNotFoundError as err:
            raise NotFoundException(
                detail=f"Schedule not found: {schedule_id}"
            ) from err

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
        try:
            result = await run_due_backups_use_case.run_schedule(schedule_id)
        except ScheduleNotFoundError as err:
            raise NotFoundException(
                detail=f"Schedule not found: {schedule_id}"
            ) from err
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
        try:
            updated = await use_case.set_enabled(schedule_id, enabled)
        except ScheduleNotFoundError as err:
            raise NotFoundException(
                detail=f"Schedule not found: {schedule_id}"
            ) from err
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
