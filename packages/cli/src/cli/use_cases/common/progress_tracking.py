"""
Progress tracking utilities for CLI operations.
"""

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class ProgressTracker:
    """
    Utility for managing progress display during CLI operations.
    """

    def __init__(self, console: Console):
        self._console = console

    @asynccontextmanager
    async def track_progress(
        self, description: str, total: int | None = None
    ) -> AsyncGenerator["ProgressTask", None]:
        """
        Context manager for tracking progress of operations.

        Args:
            description: Description of the operation
            total: Total number of items (None for indeterminate)

        Yields:
            Progress task object for updating progress
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self._console,
            transient=True,
        ) as progress:
            task = progress.add_task(description, total=total)
            yield ProgressTask(progress, task)

    @asynccontextmanager
    async def track_device_operations(
        self,
        device_ips: list[str],
        operation_name: str,
        operation_func: Callable[[str], Awaitable[Any]],
    ) -> AsyncGenerator[list[Any], None]:
        """
        Track progress while performing operations on multiple devices.

        Args:
            device_ips: List of device IP addresses
            operation_name: Name of the operation (e.g., "Checking device status")
            operation_func: Async function to call for each device IP

        Yields:
            List of results from the operations
        """
        results = []

        async with self.track_progress(
            f"{operation_name}...", total=len(device_ips)
        ) as task:
            for device_ip in device_ips:
                try:
                    result = await operation_func(device_ip)
                    results.append(result)
                except Exception as e:
                    # Return error result - let caller handle formatting
                    results.append(
                        {"ip": device_ip, "status": "error", "error": str(e)}
                    )

                task.advance()

        yield results


class ProgressTask:
    """Wrapper for progress task operations."""

    def __init__(self, progress: Progress, task_id: Any):
        self._progress = progress
        self._task_id = task_id

    def advance(self, amount: int = 1) -> None:
        """Advance the progress by specified amount."""
        self._progress.advance(self._task_id, amount)

    def update(self, description: str) -> None:
        """Update the task description."""
        self._progress.update(self._task_id, description=description)
