"""
Bulk operations CLI use case.
"""

from rich.console import Console

from cli.dependencies.container import CLIContainer
from cli.entities.bulk import (
    BulkConfigApplyRequest,
    BulkConfigExportRequest,
    BulkOperationRequest,
)

from ..common.device_discovery import DeviceDiscoveryRequest, DeviceDiscoveryUseCase


class BulkOperationsUseCase:
    """CLI use case for bulk operations on devices."""

    def __init__(self, container: CLIContainer, console: Console):
        self._container = container
        self._console = console
        self._device_discovery = DeviceDiscoveryUseCase(container)
        self._bulk_operations_interactor = container.get_bulk_operations_interactor()

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
