"""
Bulk operations CLI use case.
"""

import logging
import time

from rich.console import Console

from cli.dependencies.container import CLIContainer
from cli.entities.bulk import (
    BulkConfigApplyRequest,
    BulkConfigExportRequest,
    BulkOperationRequest,
    BulkOperationResult,
    BulkRebootRequest,
    BulkRebootResult,
)

from ..common.device_discovery import DeviceDiscoveryRequest, DeviceDiscoveryUseCase
from ..common.progress_tracking import ProgressTracker
from ..common.result_formatting import ResultFormatter

logger = logging.getLogger(__name__)


class BulkOperationsUseCase:
    """CLI use case for bulk operations on devices."""

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._device_discovery = DeviceDiscoveryUseCase(container)
        self._bulk_operations_interactor = container.get_bulk_operations_interactor()
        self._progress_tracker = ProgressTracker(console)
        self._result_formatter = ResultFormatter(console)

    async def execute_bulk_reboot(self, request: BulkRebootRequest) -> BulkRebootResult:
        start_time = time.time()

        device_ips = await self._resolve_device_ips(request)

        if not device_ips:
            return BulkRebootResult(
                success=False,
                message="No devices found or specified",
                total_devices=0,
                successful_operations=0,
                failed_operations=0,
            )

        if not request.force:
            if (
                not self._console.input(
                    f"[yellow]Reboot {len(device_ips)} device(s)? (y/N): [/yellow]"
                )
                .lower()
                .startswith("y")
            ):
                return BulkRebootResult(
                    success=False,
                    message="Operation cancelled by user",
                    total_devices=len(device_ips),
                    successful_operations=0,
                    failed_operations=0,
                )

        async with self._progress_tracker.track_bulk_operation(
            "Rebooting devices", len(device_ips)
        ):
            try:
                results = await self._bulk_operations_interactor.execute_bulk_reboot(
                    device_ips
                )

                successful = sum(1 for r in results if r.success)
                failed = len(results) - successful

                device_results = {}
                errors_by_device = {}

                for result in results:
                    from cli.entities.common import OperationResult

                    device_results[result.device_ip] = OperationResult(
                        success=result.success,
                        message=result.message,
                        error=result.error,
                    )

                    if not result.success and result.error:
                        errors_by_device[result.device_ip] = result.error

                return BulkRebootResult(
                    success=failed == 0,
                    message=f"Completed: {successful} successful, {failed} failed",
                    total_devices=len(device_ips),
                    successful_operations=successful,
                    failed_operations=failed,
                    device_results=device_results,
                    errors_by_device=errors_by_device,
                    time_taken_seconds=time.time() - start_time,
                    reboot_order=device_ips,
                    stagger_delay_used=request.stagger_delay,
                )

            except Exception as e:
                logger.error(f"Bulk reboot failed: {e}")
                return BulkRebootResult(
                    success=False,
                    message=f"Bulk reboot failed: {str(e)}",
                    total_devices=len(device_ips),
                    successful_operations=0,
                    failed_operations=len(device_ips),
                    time_taken_seconds=time.time() - start_time,
                )

    async def execute_bulk_update(
        self, request: BulkOperationRequest, channel: str = "stable"
    ) -> BulkOperationResult:
        start_time = time.time()

        device_ips = await self._resolve_device_ips(request)

        if not device_ips:
            return BulkOperationResult(
                success=False,
                message="No devices found or specified",
                total_devices=0,
                successful_operations=0,
                failed_operations=0,
                operation_type="bulk_update",
            )

        if not request.force:
            if (
                not self._console.input(
                    f"[yellow]Update firmware on {len(device_ips)} device(s) using {channel} channel? (y/N): [/yellow]"
                )
                .lower()
                .startswith("y")
            ):
                return BulkOperationResult(
                    success=False,
                    message="Operation cancelled by user",
                    total_devices=len(device_ips),
                    successful_operations=0,
                    failed_operations=0,
                    operation_type="bulk_update",
                )

        async with self._progress_tracker.track_bulk_operation(
            "Updating firmware", len(device_ips)
        ):
            try:
                results = await self._bulk_operations_interactor.execute_bulk_update(
                    device_ips, channel
                )

                successful = sum(1 for r in results if r.success)
                failed = len(results) - successful

                device_results = {}
                errors_by_device = {}

                for result in results:
                    from cli.entities.common import OperationResult

                    device_results[result.device_ip] = OperationResult(
                        success=result.success,
                        message=result.message,
                        error=result.error,
                    )

                    if not result.success and result.error:
                        errors_by_device[result.device_ip] = result.error

                return BulkOperationResult(
                    success=failed == 0,
                    message=f"Completed: {successful} successful, {failed} failed",
                    total_devices=len(device_ips),
                    successful_operations=successful,
                    failed_operations=failed,
                    device_results=device_results,
                    errors_by_device=errors_by_device,
                    operation_type="bulk_update",
                    time_taken_seconds=time.time() - start_time,
                )

            except Exception as e:
                logger.error(f"Bulk update failed: {e}")
                return BulkOperationResult(
                    success=False,
                    message=f"Bulk update failed: {str(e)}",
                    total_devices=len(device_ips),
                    successful_operations=0,
                    failed_operations=len(device_ips),
                    operation_type="bulk_update",
                    time_taken_seconds=time.time() - start_time,
                )

    async def _resolve_device_ips(self, request: BulkOperationRequest) -> list[str]:
        if not request.targets:
            return []

        discovery_request = DeviceDiscoveryRequest(
            targets=request.targets,
            timeout=request.timeout,
            workers=request.workers,
        )

        device_list = await self._device_discovery.discover_devices(discovery_request)
        return [d.ip for d in device_list]

    def display_bulk_results(self, result: BulkOperationResult) -> None:
        self._result_formatter.display_bulk_operation_result(result)

    async def execute_bulk_config_export(
        self, request: BulkConfigExportRequest
    ) -> dict:
        device_ips = await self._resolve_device_ips(request)

        if not device_ips:
            raise ValueError("No devices found or specified")

        return await self._bulk_operations_interactor.export_bulk_config(
            device_ips, request.component_types
        )

    async def execute_bulk_config_apply(self, request: BulkConfigApplyRequest) -> list:
        device_ips = await self._resolve_device_ips(request)

        if not device_ips:
            raise ValueError("No devices found or specified")

        if request.config_data is None:
            raise ValueError("No configuration data provided")

        return await self._bulk_operations_interactor.apply_bulk_config(
            device_ips, request.component_type, request.config_data
        )
