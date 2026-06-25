"""Tests for the backup schedules API controller."""

from api.controllers.backup_schedules import BackupSchedulesController
from core.domain.entities.backup_schedule import BackupSchedule
from core.use_cases.manage_backup_schedules import (
    ManageBackupSchedulesUseCase,
    ScheduleAlreadyExistsError,
    ScheduleNotFoundError,
)
from core.use_cases.run_due_backups import RunDueBackupsUseCase, ScheduleRunResult
from litestar.di import Provide
from litestar.testing import create_test_client


def _manage_provider(use_case):
    return {
        "manage_schedules_use_case": Provide(lambda: use_case, sync_to_thread=False)
    }


def _run_provider(use_case):
    return {"run_due_backups_use_case": Provide(lambda: use_case, sync_to_thread=False)}


def _schedule(**kwargs):
    base = {"id": 1, "name": "nightly", "interval_seconds": 3600, "next_run_at": 1000}
    base.update(kwargs)
    return BackupSchedule(**base)


class TestBackupSchedulesController:
    def test_it_lists_schedules(self):
        class Mock(ManageBackupSchedulesUseCase):
            def __init__(self):
                pass

            async def list_schedules(self):
                return [_schedule()]

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_manage_provider(Mock()),
        ) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert response.json()[0]["name"] == "nightly"

    def test_it_creates_with_preset_cadence(self):
        captured = {}

        class Mock(ManageBackupSchedulesUseCase):
            def __init__(self):
                pass

            async def create_schedule(self, schedule):
                captured["interval"] = schedule.interval_seconds
                schedule.id = 5
                return schedule

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_manage_provider(Mock()),
        ) as client:
            response = client.post(
                "/",
                json={
                    "name": "daily-job",
                    "every": "daily",
                    "target_ips": ["192.168.1.10"],
                },
            )
            assert response.status_code == 201
            assert response.json()["id"] == 5
            assert captured["interval"] == 86400

    def test_it_rejects_schedule_without_targets(self):
        class Mock(ManageBackupSchedulesUseCase):
            def __init__(self):
                pass

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_manage_provider(Mock()),
        ) as client:
            response = client.post("/", json={"name": "no-targets", "every": "daily"})
            assert response.status_code in (400, 500)

    def test_it_rejects_both_cadence_sources(self):
        class Mock(ManageBackupSchedulesUseCase):
            def __init__(self):
                pass

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_manage_provider(Mock()),
        ) as client:
            response = client.post(
                "/",
                json={
                    "name": "ambiguous",
                    "every": "daily",
                    "interval_seconds": 3600,
                    "target_ips": ["192.168.1.10"],
                },
            )
            assert response.status_code in (400, 500)

    def test_it_returns_409_on_duplicate_name(self):
        class Mock(ManageBackupSchedulesUseCase):
            def __init__(self):
                pass

            async def create_schedule(self, schedule):
                raise ScheduleAlreadyExistsError(schedule.name)

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_manage_provider(Mock()),
        ) as client:
            response = client.post(
                "/",
                json={
                    "name": "dupe",
                    "every": "daily",
                    "target_ips": ["192.168.1.10"],
                },
            )
            assert response.status_code == 409

    def test_it_returns_404_on_missing_get(self):
        class Mock(ManageBackupSchedulesUseCase):
            def __init__(self):
                pass

            async def get_schedule(self, schedule_id):
                raise ScheduleNotFoundError(schedule_id)

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_manage_provider(Mock()),
        ) as client:
            response = client.get("/99")
            assert response.status_code == 404

    def test_it_rejects_update_that_clears_all_targets(self):
        existing = _schedule(
            target_ips=["192.168.1.10"], target_macs=[], all_credentialed=False
        )

        class Mock(ManageBackupSchedulesUseCase):
            def __init__(self):
                pass

            async def get_schedule(self, schedule_id):
                return existing

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_manage_provider(Mock()),
        ) as client:
            response = client.put(
                "/1",
                json={
                    "target_ips": [],
                    "target_macs": [],
                    "all_credentialed": False,
                },
            )
            assert response.status_code == 400

    def test_it_disables_a_schedule(self):
        class Mock(ManageBackupSchedulesUseCase):
            def __init__(self):
                pass

            async def set_enabled(self, schedule_id, enabled):
                return _schedule(id=schedule_id, enabled=enabled)

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_manage_provider(Mock()),
        ) as client:
            response = client.post("/1/disable")
            assert response.status_code == 201
            assert response.json()["enabled"] is False

    def test_it_runs_a_schedule_now(self):
        class Mock(RunDueBackupsUseCase):
            def __init__(self):
                pass

            async def run_schedule(self, schedule_id):
                return ScheduleRunResult(
                    schedule_id=schedule_id,
                    schedule_name="nightly",
                    status="ok",
                    targets=2,
                    ok=2,
                    message="2 ok, 0 failed, 0 skipped",
                )

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_run_provider(Mock()),
        ) as client:
            response = client.post("/1/run")
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "ok"
            assert data["ok"] == 2

    def test_it_returns_404_running_missing_schedule(self):
        class Mock(RunDueBackupsUseCase):
            def __init__(self):
                pass

            async def run_schedule(self, schedule_id):
                raise ScheduleNotFoundError(schedule_id)

        with create_test_client(
            route_handlers=[BackupSchedulesController],
            dependencies=_run_provider(Mock()),
        ) as client:
            response = client.post("/99/run")
            assert response.status_code == 404
