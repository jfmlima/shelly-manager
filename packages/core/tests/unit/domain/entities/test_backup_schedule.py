"""Tests for the BackupSchedule entity's next-run arithmetic."""

from core.domain.entities.backup_schedule import BackupSchedule


def _schedule(interval=3600, next_run_at=None):
    return BackupSchedule(
        name="nightly",
        interval_seconds=interval,
        next_run_at=next_run_at,
    )


class TestComputeNextRun:
    def test_it_future_next_run_is_unchanged(self):
        schedule = _schedule(interval=3600, next_run_at=2000)
        assert schedule.compute_next_run(1000) == 2000

    def test_it_boundary_next_run_equal_to_now_advances_one_interval(self):
        schedule = _schedule(interval=100, next_run_at=1000)
        assert schedule.compute_next_run(1000) == 1100

    def test_it_far_past_next_run_fires_once_on_the_grid(self):
        # Anchored at 100, interval 100, now 350: the next slot strictly after now
        # is 400, not a backfill of 200/300/400.
        schedule = _schedule(interval=100, next_run_at=100)
        assert schedule.compute_next_run(350) == 400

    def test_it_none_next_run_anchors_on_now(self):
        schedule = _schedule(interval=3600, next_run_at=None)
        assert schedule.compute_next_run(1000) == 4600

    def test_it_non_positive_interval_never_loops(self):
        schedule = _schedule(interval=0, next_run_at=10)
        assert schedule.compute_next_run(1000) == 1001
