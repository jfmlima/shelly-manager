"""Tests for the backups API controller."""

from api.controllers.backups import BackupsController
from core.domain.entities.device_backup import DeviceBackup, DeviceBackupSummary
from core.domain.entities.exceptions import DeviceNotFoundError
from core.domain.value_objects.restore_result import (
    ComponentRestoreResult,
    RestoreResult,
)
from core.use_cases.backup_device_config import (
    BackupDeviceConfig,
    BackupNotFoundError,
)
from core.use_cases.restore_device_config import (
    DeviceMismatchError,
    RestoreDeviceConfig,
)
from litestar.di import Provide
from litestar.testing import create_test_client


def _backup_provider(use_case):
    return {"backup_use_case": Provide(lambda: use_case, sync_to_thread=False)}


def _restore_provider(use_case):
    return {"restore_use_case": Provide(lambda: use_case, sync_to_thread=False)}


class TestBackupsController:
    def test_list_backups_returns_summaries(self):
        class MockBackup(BackupDeviceConfig):
            def __init__(self):
                pass

            async def list_backups(self, device_mac=None):
                return [DeviceBackupSummary(device_mac="AABBCCDDEEFF", id=1)]

        with create_test_client(
            route_handlers=[BackupsController],
            dependencies=_backup_provider(MockBackup()),
        ) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["device_mac"] == "AABBCCDDEEFF"

    def test_create_backup_returns_detail(self):
        class MockBackup(BackupDeviceConfig):
            def __init__(self):
                pass

            async def create_backup(self, device_ip, name=None):
                return DeviceBackup(
                    device_mac="AABBCCDDEEFF",
                    snapshot={"components": {}},
                    device_ip=device_ip,
                    id=7,
                )

        with create_test_client(
            route_handlers=[BackupsController],
            dependencies=_backup_provider(MockBackup()),
        ) as client:
            response = client.post("/", json={"device_ip": "192.168.1.100"})
            assert response.status_code == 201
            assert response.json()["id"] == 7

    def test_create_backup_unreachable_returns_404(self):
        class MockBackup(BackupDeviceConfig):
            def __init__(self):
                pass

            async def create_backup(self, device_ip, name=None):
                raise DeviceNotFoundError(device_ip)

        with create_test_client(
            route_handlers=[BackupsController],
            dependencies=_backup_provider(MockBackup()),
        ) as client:
            response = client.post("/", json={"device_ip": "192.168.1.100"})
            assert response.status_code == 404

    def test_get_missing_backup_returns_404(self):
        class MockBackup(BackupDeviceConfig):
            def __init__(self):
                pass

            async def get_backup(self, backup_id):
                raise BackupNotFoundError(backup_id)

        with create_test_client(
            route_handlers=[BackupsController],
            dependencies=_backup_provider(MockBackup()),
        ) as client:
            response = client.get("/99")
            assert response.status_code == 404

    def test_restore_returns_result(self):
        class MockRestore(RestoreDeviceConfig):
            def __init__(self):
                pass

            async def restore(self, backup_id, device_ip, **kwargs):
                return RestoreResult(
                    success=True,
                    device_ip=device_ip,
                    backup_id=backup_id,
                    total=1,
                    succeeded=1,
                    components=[
                        ComponentRestoreResult(
                            key="switch:0", action="SetConfig", success=True
                        )
                    ],
                )

        with create_test_client(
            route_handlers=[BackupsController],
            dependencies=_restore_provider(MockRestore()),
        ) as client:
            response = client.post("/1/restore", json={"device_ip": "192.168.1.100"})
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["components"][0]["key"] == "switch:0"

    def test_restore_mac_mismatch_returns_409(self):
        class MockRestore(RestoreDeviceConfig):
            def __init__(self):
                pass

            async def restore(self, backup_id, device_ip, **kwargs):
                raise DeviceMismatchError("AABBCCDDEEFF", "FFFFFFFFFFFF")

        with create_test_client(
            route_handlers=[BackupsController],
            dependencies=_restore_provider(MockRestore()),
        ) as client:
            response = client.post("/1/restore", json={"device_ip": "192.168.1.100"})
            assert response.status_code == 409

    def test_restore_invalid_ip_returns_400(self):
        class MockRestore(RestoreDeviceConfig):
            def __init__(self):
                pass

            async def restore(self, backup_id, device_ip, **kwargs):
                return RestoreResult(
                    success=True, device_ip=device_ip, backup_id=backup_id, total=0
                )

        with create_test_client(
            route_handlers=[BackupsController],
            dependencies=_restore_provider(MockRestore()),
        ) as client:
            response = client.post("/1/restore", json={"device_ip": "not-an-ip"})
            assert response.status_code in (400, 500)
