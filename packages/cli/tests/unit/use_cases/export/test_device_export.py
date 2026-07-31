from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.use_cases.export.device_export import DeviceExportUseCase
from core.domain.entities.config_snapshot import EXPORTABLE_COMPONENT_TYPES


class TestDeviceExportConfiguration:
    @pytest.fixture
    def bulk_operations(self):
        bulk = AsyncMock()
        bulk.export_bulk_config.return_value = {"devices": {}}
        return bulk

    @pytest.fixture
    def export_use_case(self, bulk_operations):
        container = MagicMock()
        container.get_bulk_operations_interactor.return_value = bulk_operations
        return DeviceExportUseCase(container, MagicMock())

    @pytest.mark.asyncio
    async def test_it_exports_every_exportable_component_type(
        self, export_use_case, bulk_operations
    ):
        device = MagicMock()
        device.device_ip = "192.168.1.100"

        await export_use_case._get_configurations_for_devices([device])

        # The caller swallows every exception, so an export that never reached
        # the device would otherwise read here as an unsubscriptable None.
        bulk_operations.export_bulk_config.assert_awaited_once()

        _, requested_types = bulk_operations.export_bulk_config.call_args[0]
        assert set(requested_types) == EXPORTABLE_COMPONENT_TYPES
