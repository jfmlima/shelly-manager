from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.device_backup import DeviceBackupSummary
from core.domain.entities.exceptions import DeviceNotFoundError
from core.use_cases.backup_device_config import (
    BackupDeviceConfig,
    BackupError,
    BackupNotFoundError,
)


def _status(mac="AABBCCDDEEFF", app_name="Plus1PM", components=None, gen=2):
    return SimpleNamespace(
        components=components
        or [
            SimpleNamespace(component_type="switch", key="switch:0"),
            SimpleNamespace(component_type="sys", key="sys"),
        ],
        mac_address=mac,
        app_name=app_name,
        gen=gen,
        device_name="Test Device",
        device_type="SNSW-001P16EU",
        firmware_version="1.0.0",
    )


def _export(ip="192.168.1.100"):
    return {
        "devices": {
            ip: {
                "device_info": {"mac_address": "AABBCCDDEEFF"},
                "components": {
                    "switch:0": {"type": "switch", "success": True, "config": {}},
                    "sys": {"type": "sys", "success": True, "config": {}},
                },
            }
        }
    }


class TestBackupDeviceConfig:
    @pytest.fixture
    def mock_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_bulk_operations(self):
        bulk = AsyncMock()
        bulk.export_bulk_config = AsyncMock(return_value=_export())
        return bulk

    @pytest.fixture
    def use_case(self, mock_device_gateway, mock_bulk_operations, mock_repository):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        return BackupDeviceConfig(
            device_gateway=mock_device_gateway,
            bulk_operations=mock_bulk_operations,
            repository_factory=repository_factory,
        )

    async def test_it_creates_a_backup_and_persists_it(
        self, use_case, mock_device_gateway, mock_bulk_operations, mock_repository
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_repository.create = AsyncMock(side_effect=lambda backup: backup)

        backup = await use_case.create_backup("192.168.1.100", name="nightly")

        assert backup.device_mac == "AABBCCDDEEFF"
        assert backup.generation == "gen2"
        assert backup.name == "nightly"
        assert backup.source == "manual"
        # schedules always added to the requested component types
        called_types = mock_bulk_operations.export_bulk_config.call_args.args[1]
        assert "schedules" in called_types
        assert "switch" in called_types and "sys" in called_types
        mock_repository.create.assert_awaited_once()

    async def test_it_detects_gen1_from_gen_field(
        self, use_case, mock_device_gateway, mock_repository
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status(gen=1))
        mock_repository.create = AsyncMock(side_effect=lambda backup: backup)

        backup = await use_case.create_backup("192.168.1.100")

        assert backup.generation == "gen1"

    async def test_it_raises_when_generation_unknown(
        self, use_case, mock_device_gateway
    ):
        # gen could not be determined (e.g. GetDeviceInfo partially failed).
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(gen=None)
        )

        with pytest.raises(BackupError):
            await use_case.create_backup("192.168.1.100")

    async def test_it_raises_when_all_components_failed(
        self, use_case, mock_device_gateway, mock_bulk_operations
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_bulk_operations.export_bulk_config = AsyncMock(
            return_value={
                "devices": {
                    "192.168.1.100": {
                        "device_info": {"mac_address": "AABBCCDDEEFF"},
                        "components": {
                            "switch:0": {
                                "type": "switch",
                                "success": False,
                                "config": None,
                                "error": "boom",
                            }
                        },
                    }
                }
            }
        )

        with pytest.raises(BackupError):
            await use_case.create_backup("192.168.1.100")

    async def test_it_raises_when_only_scripts_without_code(
        self, use_case, mock_device_gateway, mock_bulk_operations
    ):
        # GetConfig succeeded for the script but GetCode failed, so no `code` —
        # not actually restorable, even though config is present.
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_bulk_operations.export_bulk_config = AsyncMock(
            return_value={
                "devices": {
                    "192.168.1.100": {
                        "device_info": {"mac_address": "AABBCCDDEEFF"},
                        "components": {
                            "script:1": {
                                "type": "script",
                                "success": True,
                                "config": {"id": 1, "enable": True},
                            }
                        },
                    }
                }
            }
        )

        with pytest.raises(BackupError):
            await use_case.create_backup("192.168.1.100")

    async def test_it_accepts_script_with_empty_code_body(
        self, use_case, mock_device_gateway, mock_bulk_operations, mock_repository
    ):
        # An empty script body ("") is valid and restorable.
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_repository.create = AsyncMock(side_effect=lambda backup: backup)
        mock_bulk_operations.export_bulk_config = AsyncMock(
            return_value={
                "devices": {
                    "192.168.1.100": {
                        "device_info": {"mac_address": "AABBCCDDEEFF"},
                        "components": {
                            "script:1": {
                                "type": "script",
                                "success": True,
                                "config": {"id": 1},
                                "code": {"data": ""},
                            }
                        },
                    }
                }
            }
        )

        backup = await use_case.create_backup("192.168.1.100")

        assert backup.id is not None or backup.device_mac == "AABBCCDDEEFF"
        mock_repository.create.assert_awaited_once()

    async def test_it_raises_when_device_unreachable(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        with pytest.raises(DeviceNotFoundError):
            await use_case.create_backup("192.168.1.100")

    async def test_it_raises_when_export_drops_the_device(
        self, use_case, mock_device_gateway, mock_bulk_operations
    ):
        # First status fetch succeeds, but export's own fetch drops the device.
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_bulk_operations.export_bulk_config = AsyncMock(
            return_value={"devices": {}}
        )

        with pytest.raises(DeviceNotFoundError):
            await use_case.create_backup("192.168.1.100")

    async def test_it_raises_when_export_block_has_no_components(
        self, use_case, mock_device_gateway, mock_bulk_operations
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_bulk_operations.export_bulk_config = AsyncMock(
            return_value={
                "devices": {"192.168.1.100": {"device_info": {}, "components": {}}}
            }
        )

        with pytest.raises(BackupError):
            await use_case.create_backup("192.168.1.100")

    async def test_it_raises_backup_error_without_mac(
        self, use_case, mock_device_gateway, mock_bulk_operations
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(mac=None)
        )
        mock_bulk_operations.export_bulk_config = AsyncMock(
            return_value={
                "devices": {
                    "192.168.1.100": {
                        "device_info": {},
                        "components": {
                            "sys": {"type": "sys", "success": True, "config": {}}
                        },
                    }
                }
            }
        )

        with pytest.raises(BackupError):
            await use_case.create_backup("192.168.1.100")

    async def test_it_lists_backups(self, use_case, mock_repository):
        mock_repository.list_summaries = AsyncMock(
            return_value=[DeviceBackupSummary(device_mac="AABBCCDDEEFF", id=1)]
        )

        result = await use_case.list_backups("AA:BB:CC:DD:EE:FF")

        assert len(result) == 1
        mock_repository.list_summaries.assert_awaited_once_with("AA:BB:CC:DD:EE:FF")

    async def test_it_lists_a_page_with_total(self, use_case, mock_repository):
        mock_repository.list_summaries = AsyncMock(
            return_value=[DeviceBackupSummary(device_mac="AABBCCDDEEFF", id=3)]
        )
        mock_repository.count_summaries = AsyncMock(return_value=7)

        page = await use_case.list_backups_page("AA:BB:CC:DD:EE:FF", limit=1, offset=2)

        assert [s.id for s in page.items] == [3]
        assert page.total == 7
        assert page.limit == 1
        assert page.offset == 2
        mock_repository.list_summaries.assert_awaited_once_with(
            "AA:BB:CC:DD:EE:FF", 1, 2
        )
        mock_repository.count_summaries.assert_awaited_once_with("AA:BB:CC:DD:EE:FF")

    async def test_it_raises_when_backup_missing_on_get(
        self, use_case, mock_repository
    ):
        mock_repository.get = AsyncMock(return_value=None)

        with pytest.raises(BackupNotFoundError):
            await use_case.get_backup(99)

    async def test_it_raises_when_deleting_missing_backup(
        self, use_case, mock_repository
    ):
        mock_repository.delete = AsyncMock(return_value=False)

        with pytest.raises(BackupNotFoundError):
            await use_case.delete_backup(99)

    async def test_it_deletes_existing_backup(self, use_case, mock_repository):
        mock_repository.delete = AsyncMock(return_value=True)

        await use_case.delete_backup(5)

        mock_repository.delete.assert_awaited_once_with(5)
