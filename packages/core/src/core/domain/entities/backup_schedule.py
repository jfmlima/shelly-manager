"""Domain entity for an automated backup schedule."""

from dataclasses import dataclass, field


@dataclass
class BackupSchedule:
    """A recurring, interval-based backup job over a set of target devices.

    Targets are the union of three modes: explicit ``target_ips``, ``target_macs``
    (resolved to an IP via the credentials store's last-seen IP), and
    ``all_credentialed`` (every MAC we hold credentials for). MACs with no known IP
    are reported skipped, never failed.
    """

    name: str
    interval_seconds: int
    id: int | None = None
    target_ips: list[str] = field(default_factory=list)
    target_macs: list[str] = field(default_factory=list)
    all_credentialed: bool = False
    enabled: bool = True
    retention_keep_last: int | None = None
    retention_max_age_days: int | None = None
    last_run_at: int | None = None
    next_run_at: int | None = None
    last_status: str | None = None
    created_at: int | None = None
    updated_at: int | None = None

    def compute_next_run(self, from_ts: int) -> int:
        """Return the next run timestamp strictly after ``from_ts``.

        Advances along the interval grid anchored on the current ``next_run_at`` so
        a backup that fell behind (device offline for days) fires once on catch-up
        rather than backfilling every missed slot. Computed arithmetically to stay
        O(1) even when the gap spans a very long offline period.
        """
        interval = self.interval_seconds
        if interval <= 0:
            # Defensive: validation enforces interval >= 1, but never loop forever.
            return from_ts + 1

        anchor = self.next_run_at if self.next_run_at is not None else from_ts
        if anchor > from_ts:
            return anchor
        steps = (from_ts - anchor) // interval + 1
        return anchor + steps * interval
