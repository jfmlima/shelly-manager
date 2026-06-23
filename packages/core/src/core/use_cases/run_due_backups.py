"""Use case for running due scheduled backups with retention."""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime

from core.domain.entities.backup_schedule import BackupSchedule
from core.domain.entities.exceptions import DeviceNotFoundError
from core.domain.value_objects.scan_request import ScanRequest
from core.repositories.backup_repository import BackupRepository
from core.repositories.backup_schedule_repository import BackupScheduleRepository
from core.repositories.credentials_repository import CredentialsRepository
from core.use_cases.backup_device_config import BackupDeviceConfig
from core.use_cases.manage_backup_schedules import ScheduleNotFoundError
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.utils.validation import normalize_mac

logger = logging.getLogger(__name__)

SECONDS_PER_DAY = 86400


def _default_clock() -> int:
    return int(datetime.now(UTC).timestamp())


@dataclass
class ScheduleRunResult:
    """Outcome of running a single schedule once."""

    schedule_id: int
    schedule_name: str
    status: str
    targets: int = 0
    ok: int = 0
    failed: int = 0
    skipped: int = 0
    message: str = ""


class RunDueBackupsUseCase:
    """Run schedules that are due and prune snapshots per their retention policy.

    The scheduler has no HTTP request, so every repository access opens its own
    session via the injected factories. The ``clock`` is injectable purely so the
    runner is deterministic under test.
    """

    def __init__(
        self,
        schedule_repository_factory: Callable[
            [], AbstractAsyncContextManager[BackupScheduleRepository]
        ],
        backup_repository_factory: Callable[
            [], AbstractAsyncContextManager[BackupRepository]
        ],
        credentials_repository_factory: Callable[
            [], AbstractAsyncContextManager[CredentialsRepository]
        ],
        backup_device_config: BackupDeviceConfig,
        scan_devices: ScanDevicesUseCase | None = None,
        clock: Callable[[], int] = _default_clock,
    ):
        self._schedule_repository_factory = schedule_repository_factory
        self._backup_repository_factory = backup_repository_factory
        self._credentials_repository_factory = credentials_repository_factory
        self._backup_device_config = backup_device_config
        self._scan_devices = scan_devices
        self._clock = clock

    async def run_due(self) -> list[ScheduleRunResult]:
        """Run every schedule whose next_run_at has passed, sequentially."""
        now = self._clock()
        async with self._schedule_repository_factory() as repository:
            due = await repository.list_due(now)
        results: list[ScheduleRunResult] = []
        # Sequential on purpose: backing up many devices at once would hammer the LAN.
        for schedule in due:
            results.append(await self._run_one(schedule, now))
        return results

    async def run_schedule(self, schedule_id: int) -> ScheduleRunResult:
        """Run one schedule now, ignoring its next_run_at.

        Raises:
            ScheduleNotFoundError: If the schedule does not exist.
        """
        async with self._schedule_repository_factory() as repository:
            schedule = await repository.get(schedule_id)
        if schedule is None:
            raise ScheduleNotFoundError(schedule_id)
        return await self._run_one(schedule, self._clock())

    async def _run_one(self, schedule: BackupSchedule, now: int) -> ScheduleRunResult:
        target_ips, skipped_macs = await self._resolve_targets(schedule)
        ok = 0
        failed = 0
        skipped = len(skipped_macs)
        touched_macs: set[str] = set()

        for ip in target_ips:
            try:
                backup = await self._backup_device_config.create_backup(
                    ip, source="scheduled"
                )
                ok += 1
                touched_macs.add(normalize_mac(backup.device_mac))
            except DeviceNotFoundError:
                skipped += 1
                logger.warning(
                    "Schedule '%s': device %s unreachable, skipped",
                    schedule.name,
                    ip,
                )
            except Exception:
                failed += 1
                logger.exception(
                    "Schedule '%s': backup failed for %s", schedule.name, ip
                )

        await self._apply_retention(schedule, touched_macs, now)

        status = self._classify(ok, failed, skipped)
        message = f"{ok} ok, {failed} failed, {skipped} skipped"
        if schedule.id is not None:
            next_run = schedule.compute_next_run(now)
            async with self._schedule_repository_factory() as repository:
                await repository.set_run_result(
                    schedule.id,
                    last_run_at=now,
                    next_run_at=next_run,
                    last_status=f"{status}: {message}",
                )

        return ScheduleRunResult(
            schedule_id=schedule.id or 0,
            schedule_name=schedule.name,
            status=status,
            targets=len(target_ips),
            ok=ok,
            failed=failed,
            skipped=skipped,
            message=message,
        )

    async def _resolve_targets(
        self, schedule: BackupSchedule
    ) -> tuple[list[str], list[str]]:
        """Resolve a schedule's targets to a deduped IP list plus unresolved MACs.

        Union of explicit IPs, range/CIDR targets expanded by scanning for live
        Shelly devices, MACs resolved via the credentials store's last-seen IP, and
        (optionally) every credentialed MAC. A MAC with no known IP is returned as
        skipped rather than silently dropped.
        """
        ips = {t for t in schedule.target_ips if t and not _is_discoverable_target(t)}
        discover_targets = [
            t for t in schedule.target_ips if t and _is_discoverable_target(t)
        ]
        if discover_targets:
            ips |= await self._discover_targets(schedule, discover_targets)

        requested_macs = {normalize_mac(m) for m in schedule.target_macs if m}
        skipped_macs: list[str] = []

        if schedule.all_credentialed or requested_macs:
            async with self._credentials_repository_factory() as repository:
                credentials = await repository.list_all()
            by_mac = {c.mac: c for c in credentials if c is not None and c.mac != "*"}

            macs = set(requested_macs)
            if schedule.all_credentialed:
                macs |= set(by_mac.keys())

            for mac in sorted(macs):
                credential = by_mac.get(mac)
                if credential and credential.last_seen_ip:
                    ips.add(credential.last_seen_ip)
                else:
                    skipped_macs.append(mac)

        return sorted(ips), skipped_macs

    async def _discover_targets(
        self, schedule: BackupSchedule, targets: list[str]
    ) -> set[str]:
        """Scan range/CIDR targets and return the IPs of the Shelly devices found.

        Only discovered devices are backed up, so a /24 never turns into hundreds of
        backup attempts against IPs that hold no device.
        """
        if self._scan_devices is None:
            logger.warning(
                "Schedule '%s': targets %s need discovery but no scanner is "
                "configured; skipping them",
                schedule.name,
                targets,
            )
            return set()
        try:
            devices = await self._scan_devices.execute(ScanRequest(targets=targets))
        except Exception:
            logger.exception(
                "Schedule '%s': discovery scan failed for %s",
                schedule.name,
                targets,
            )
            return set()
        return {device.ip for device in devices if device.ip}

    async def _apply_retention(
        self, schedule: BackupSchedule, touched_macs: set[str], now: int
    ) -> None:
        if not touched_macs:
            return
        if (
            schedule.retention_keep_last is None
            and schedule.retention_max_age_days is None
        ):
            return

        async with self._backup_repository_factory() as repository:
            for mac in sorted(touched_macs):
                try:
                    if schedule.retention_keep_last is not None:
                        deleted = await repository.delete_keeping_latest_n(
                            mac, schedule.retention_keep_last
                        )
                        if deleted:
                            logger.info(
                                "Retention pruned %d scheduled backups for %s "
                                "(keep_last=%d)",
                                deleted,
                                mac,
                                schedule.retention_keep_last,
                            )
                    if schedule.retention_max_age_days is not None:
                        cutoff = now - schedule.retention_max_age_days * SECONDS_PER_DAY
                        deleted = await repository.delete_older_than(mac, cutoff)
                        if deleted:
                            logger.info(
                                "Retention pruned %d scheduled backups older than "
                                "%d days for %s",
                                deleted,
                                schedule.retention_max_age_days,
                                mac,
                            )
                except Exception:
                    logger.exception(
                        "Retention failed for %s on schedule '%s'",
                        mac,
                        schedule.name,
                    )

    @staticmethod
    def _classify(ok: int, failed: int, skipped: int) -> str:
        if failed and ok:
            return "partial"
        if failed:
            return "failed"
        if ok:
            return "ok"
        if skipped:
            return "skipped"
        return "empty"


def _is_discoverable_target(target: str) -> bool:
    """True for a range or CIDR target that must be expanded by scanning."""
    return "/" in target or "-" in target
