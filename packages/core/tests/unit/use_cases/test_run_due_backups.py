"""Tests for the scheduled-backup runner."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from core.domain.credentials import Credential
from core.domain.entities.backup_schedule import BackupSchedule
from core.domain.entities.exceptions import DeviceNotFoundError
from core.use_cases.manage_backup_schedules import ScheduleNotFoundError
from core.use_cases.run_due_backups import RunDueBackupsUseCase

NOW = 1_000_000


def _factory(obj):
    @asynccontextmanager
    async def factory():
        yield obj

    return factory


def _backup_for(ip, mac="AABBCCDDEEFF"):
    return SimpleNamespace(device_mac=mac)


def _make_use_case(
    *,
    schedule_repo,
    backup_repo=None,
    credentials_repo=None,
    backup_device_config=None,
    scan_devices=None,
    clock=NOW,
):
    backup_repo = backup_repo or AsyncMock()
    credentials_repo = credentials_repo or AsyncMock(
        list_all=AsyncMock(return_value=[])
    )
    backup_device_config = backup_device_config or AsyncMock(
        create_backup=AsyncMock(
            side_effect=lambda ip, source="scheduled": _backup_for(ip)
        )
    )
    return RunDueBackupsUseCase(
        schedule_repository_factory=_factory(schedule_repo),
        backup_repository_factory=_factory(backup_repo),
        credentials_repository_factory=_factory(credentials_repo),
        backup_device_config=backup_device_config,
        scan_devices=scan_devices,
        clock=lambda: clock,
    )


def _schedule(**kwargs):
    base = {
        "id": 1,
        "name": "nightly",
        "interval_seconds": 3600,
        "target_ips": ["192.168.1.10"],
        "next_run_at": NOW - 10,
    }
    base.update(kwargs)
    return BackupSchedule(**base)


class TestRunDue:
    async def test_it_runs_only_due_schedules(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(return_value=[_schedule()]),
            set_run_result=AsyncMock(),
        )
        backup_device_config = AsyncMock(
            create_backup=AsyncMock(
                side_effect=lambda ip, source="scheduled": _backup_for(ip)
            )
        )
        use_case = _make_use_case(
            schedule_repo=schedule_repo, backup_device_config=backup_device_config
        )

        results = await use_case.run_due()

        schedule_repo.list_due.assert_awaited_once_with(NOW)
        backup_device_config.create_backup.assert_awaited_once_with(
            "192.168.1.10", source="scheduled"
        )
        assert results[0].status == "ok"
        assert results[0].ok == 1

    async def test_it_advances_next_run_strictly_into_future(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(return_value=[_schedule(next_run_at=NOW - 5000)]),
            set_run_result=AsyncMock(),
        )
        use_case = _make_use_case(schedule_repo=schedule_repo)

        await use_case.run_due()

        kwargs = schedule_repo.set_run_result.call_args.kwargs
        assert kwargs["last_run_at"] == NOW
        assert kwargs["next_run_at"] > NOW

    async def test_it_unreachable_device_is_skipped_others_still_run(self):
        def create(ip, source="scheduled"):
            if ip == "192.168.1.10":
                raise DeviceNotFoundError(ip)
            return _backup_for(ip, mac="112233445566")

        schedule_repo = AsyncMock(
            list_due=AsyncMock(
                return_value=[_schedule(target_ips=["192.168.1.10", "192.168.1.11"])]
            ),
            set_run_result=AsyncMock(),
        )
        backup_device_config = AsyncMock(create_backup=AsyncMock(side_effect=create))
        use_case = _make_use_case(
            schedule_repo=schedule_repo, backup_device_config=backup_device_config
        )

        results = await use_case.run_due()

        assert results[0].ok == 1
        assert results[0].skipped == 1
        assert results[0].failed == 0
        assert results[0].status == "ok"

    async def test_it_generic_error_counts_as_failed_and_partial(self):
        def create(ip, source="scheduled"):
            if ip == "192.168.1.11":
                raise RuntimeError("boom")
            return _backup_for(ip)

        schedule_repo = AsyncMock(
            list_due=AsyncMock(
                return_value=[_schedule(target_ips=["192.168.1.10", "192.168.1.11"])]
            ),
            set_run_result=AsyncMock(),
        )
        backup_device_config = AsyncMock(create_backup=AsyncMock(side_effect=create))
        use_case = _make_use_case(
            schedule_repo=schedule_repo, backup_device_config=backup_device_config
        )

        results = await use_case.run_due()

        assert results[0].ok == 1
        assert results[0].failed == 1
        assert results[0].status == "partial"


class TestTargetResolution:
    async def test_it_resolves_mac_via_last_seen_ip(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(
                return_value=[
                    _schedule(target_ips=[], target_macs=["AA:BB:CC:DD:EE:FF"])
                ]
            ),
            set_run_result=AsyncMock(),
        )
        credentials_repo = AsyncMock(
            list_all=AsyncMock(
                return_value=[
                    Credential(
                        mac="AABBCCDDEEFF",
                        username="admin",
                        password="x",
                        last_seen_ip="192.168.1.50",
                    )
                ]
            )
        )
        backup_device_config = AsyncMock(
            create_backup=AsyncMock(
                side_effect=lambda ip, source="scheduled": _backup_for(ip)
            )
        )
        use_case = _make_use_case(
            schedule_repo=schedule_repo,
            credentials_repo=credentials_repo,
            backup_device_config=backup_device_config,
        )

        results = await use_case.run_due()

        backup_device_config.create_backup.assert_awaited_once_with(
            "192.168.1.50", source="scheduled"
        )
        assert results[0].ok == 1

    async def test_it_mac_without_ip_is_skipped_not_failed(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(
                return_value=[_schedule(target_ips=[], target_macs=["AABBCCDDEEFF"])]
            ),
            set_run_result=AsyncMock(),
        )
        credentials_repo = AsyncMock(
            list_all=AsyncMock(
                return_value=[
                    Credential(
                        mac="AABBCCDDEEFF",
                        username="admin",
                        password="x",
                        last_seen_ip=None,
                    )
                ]
            )
        )
        backup_device_config = AsyncMock(create_backup=AsyncMock())
        use_case = _make_use_case(
            schedule_repo=schedule_repo,
            credentials_repo=credentials_repo,
            backup_device_config=backup_device_config,
        )

        results = await use_case.run_due()

        backup_device_config.create_backup.assert_not_awaited()
        assert results[0].skipped == 1
        assert results[0].status == "skipped"

    async def test_it_all_credentialed_unions_with_explicit_ips(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(
                return_value=[
                    _schedule(
                        target_ips=["192.168.1.10"],
                        all_credentialed=True,
                    )
                ]
            ),
            set_run_result=AsyncMock(),
        )
        credentials_repo = AsyncMock(
            list_all=AsyncMock(
                return_value=[
                    Credential(
                        mac="AABBCCDDEEFF",
                        username="admin",
                        password="x",
                        last_seen_ip="192.168.1.20",
                    ),
                    None,  # an undecryptable credential is ignored
                ]
            )
        )
        seen = []
        backup_device_config = AsyncMock(
            create_backup=AsyncMock(
                side_effect=lambda ip, source="scheduled": seen.append(ip)
                or _backup_for(ip)
            )
        )
        use_case = _make_use_case(
            schedule_repo=schedule_repo,
            credentials_repo=credentials_repo,
            backup_device_config=backup_device_config,
        )

        await use_case.run_due()

        assert sorted(seen) == ["192.168.1.10", "192.168.1.20"]

    async def test_it_all_credentialed_ignores_global_fallback_credential(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(
                return_value=[
                    _schedule(
                        target_ips=["192.168.1.10"],
                        all_credentialed=True,
                    )
                ]
            ),
            set_run_result=AsyncMock(),
        )
        credentials_repo = AsyncMock(
            list_all=AsyncMock(
                return_value=[
                    Credential(
                        mac="*",
                        username="admin",
                        password="x",
                    ),
                    Credential(
                        mac="AABBCCDDEEFF",
                        username="admin",
                        password="x",
                        last_seen_ip="192.168.1.20",
                    ),
                ]
            )
        )
        use_case = _make_use_case(
            schedule_repo=schedule_repo,
            credentials_repo=credentials_repo,
        )

        results = await use_case.run_due()

        assert results[0].skipped == 0
        assert results[0].ok == 2

    async def test_it_discovers_devices_for_cidr_targets(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(return_value=[_schedule(target_ips=["192.168.1.0/30"])]),
            set_run_result=AsyncMock(),
        )
        scan_devices = AsyncMock(
            execute=AsyncMock(
                return_value=[
                    SimpleNamespace(ip="192.168.1.1"),
                    SimpleNamespace(ip="192.168.1.2"),
                ]
            )
        )
        seen = []
        backup_device_config = AsyncMock(
            create_backup=AsyncMock(
                side_effect=lambda ip, source="scheduled": seen.append(ip)
                or _backup_for(ip)
            )
        )
        use_case = _make_use_case(
            schedule_repo=schedule_repo,
            backup_device_config=backup_device_config,
            scan_devices=scan_devices,
        )

        results = await use_case.run_due()

        scan_devices.execute.assert_awaited_once()
        # Only discovered device IPs are backed up; the CIDR string itself is not.
        assert sorted(seen) == ["192.168.1.1", "192.168.1.2"]
        assert results[0].ok == 2

    async def test_it_skips_cidr_targets_when_no_scanner_configured(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(return_value=[_schedule(target_ips=["192.168.1.0/30"])]),
            set_run_result=AsyncMock(),
        )
        backup_device_config = AsyncMock(create_backup=AsyncMock())
        use_case = _make_use_case(
            schedule_repo=schedule_repo,
            backup_device_config=backup_device_config,
            scan_devices=None,
        )

        results = await use_case.run_due()

        backup_device_config.create_backup.assert_not_awaited()
        assert results[0].status == "empty"


class TestRetention:
    async def test_it_retention_keep_last_and_max_age_called_with_correct_args(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(
                return_value=[
                    _schedule(retention_keep_last=3, retention_max_age_days=7)
                ]
            ),
            set_run_result=AsyncMock(),
        )
        backup_repo = AsyncMock(
            delete_keeping_latest_n=AsyncMock(return_value=0),
            delete_older_than=AsyncMock(return_value=0),
        )
        use_case = _make_use_case(schedule_repo=schedule_repo, backup_repo=backup_repo)

        await use_case.run_due()

        backup_repo.delete_keeping_latest_n.assert_awaited_once_with("AABBCCDDEEFF", 3)
        backup_repo.delete_older_than.assert_awaited_once_with(
            "AABBCCDDEEFF", NOW - 7 * 86400
        )

    async def test_it_no_retention_when_no_devices_touched(self):
        schedule_repo = AsyncMock(
            list_due=AsyncMock(return_value=[_schedule(retention_keep_last=3)]),
            set_run_result=AsyncMock(),
        )
        backup_repo = AsyncMock(delete_keeping_latest_n=AsyncMock())
        backup_device_config = AsyncMock(
            create_backup=AsyncMock(side_effect=DeviceNotFoundError("192.168.1.10"))
        )
        use_case = _make_use_case(
            schedule_repo=schedule_repo,
            backup_repo=backup_repo,
            backup_device_config=backup_device_config,
        )

        await use_case.run_due()

        backup_repo.delete_keeping_latest_n.assert_not_awaited()


class TestRunSchedule:
    async def test_it_run_schedule_ignores_next_run_at(self):
        # next_run_at far in the future, but run-now executes anyway.
        schedule = _schedule(next_run_at=NOW + 999_999)
        schedule_repo = AsyncMock(
            get=AsyncMock(return_value=schedule),
            set_run_result=AsyncMock(),
        )
        backup_device_config = AsyncMock(
            create_backup=AsyncMock(
                side_effect=lambda ip, source="scheduled": _backup_for(ip)
            )
        )
        use_case = _make_use_case(
            schedule_repo=schedule_repo, backup_device_config=backup_device_config
        )

        result = await use_case.run_schedule(1)

        backup_device_config.create_backup.assert_awaited_once()
        assert result.ok == 1

    async def test_it_run_schedule_missing_raises(self):
        schedule_repo = AsyncMock(get=AsyncMock(return_value=None))
        use_case = _make_use_case(schedule_repo=schedule_repo)

        with pytest.raises(ScheduleNotFoundError):
            await use_case.run_schedule(999)
