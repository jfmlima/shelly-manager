"""Tests for the in-process backup scheduler."""

from unittest.mock import AsyncMock

from api.scheduler import BackupScheduler


class TestBackupScheduler:
    async def test_it_starts_and_stops_cleanly(self):
        scheduler = BackupScheduler(AsyncMock(), poll_interval_seconds=60)
        assert scheduler.running is False

        scheduler.start()
        assert scheduler.running is True

        await scheduler.stop()
        assert scheduler.running is False

    async def test_it_is_idempotent_on_double_start(self):
        scheduler = BackupScheduler(AsyncMock(), poll_interval_seconds=60)
        scheduler.start()
        scheduler.start()  # must not raise (job id already exists)
        assert scheduler.running is True
        await scheduler.stop()

    async def test_it_tick_invokes_run_due(self):
        use_case = AsyncMock(run_due=AsyncMock(return_value=[]))
        scheduler = BackupScheduler(use_case)

        await scheduler._tick()

        use_case.run_due.assert_awaited_once()

    async def test_it_tick_swallows_exceptions(self):
        use_case = AsyncMock(run_due=AsyncMock(side_effect=RuntimeError("boom")))
        scheduler = BackupScheduler(use_case)

        # A failing tick must not propagate; it would otherwise kill the loop.
        await scheduler._tick()

        use_case.run_due.assert_awaited_once()

    async def test_it_stop_without_start_is_safe(self):
        scheduler = BackupScheduler(AsyncMock())
        await scheduler.stop()
        assert scheduler.running is False
