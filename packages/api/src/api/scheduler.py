"""In-process poller that runs due scheduled backups.

Wraps APScheduler's ``AsyncIOScheduler`` with a single interval job. This is only
safe because the API runs as a single uvicorn worker (see ``run_server.py``): with
multiple workers every worker would run the poller and duplicate every backup.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.use_cases.run_due_backups import RunDueBackupsUseCase

logger = logging.getLogger(__name__)

_JOB_ID = "backup-poll"


class BackupScheduler:
    def __init__(
        self,
        run_due_use_case: RunDueBackupsUseCase,
        poll_interval_seconds: int = 60,
    ):
        self._use_case = run_due_use_case
        self._poll_interval = max(1, poll_interval_seconds)
        self._scheduler = AsyncIOScheduler()
        self._started = False

    @property
    def running(self) -> bool:
        return self._started

    def start(self) -> None:
        if self._started:
            return
        self._scheduler.add_job(
            self._tick,
            trigger="interval",
            seconds=self._poll_interval,
            id=_JOB_ID,
            max_instances=1,  # never overlap ticks
            coalesce=True,  # collapse missed ticks into one
            replace_existing=True,
        )
        self._scheduler.start()
        self._started = True
        logger.info("Backup scheduler started (poll interval %ds)", self._poll_interval)

    async def _tick(self) -> None:
        # A failing tick must never tear down the scheduler; swallow and log.
        try:
            results = await self._use_case.run_due()
            if results:
                logger.info("Backup scheduler ran %d due schedule(s)", len(results))
        except Exception:
            logger.exception("Backup scheduler tick failed")

    async def stop(self) -> None:
        if not self._started:
            return
        self._scheduler.shutdown(wait=False)
        self._started = False
        logger.info("Backup scheduler stopped")
