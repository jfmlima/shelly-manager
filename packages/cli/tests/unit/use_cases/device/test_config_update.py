from unittest.mock import AsyncMock, MagicMock

import pytest
from cli.entities import DeviceConfigUpdateRequest
from cli.use_cases.device.config_update import ConfigUpdateUseCase


class TestConfigUpdateUseCase:
    @pytest.fixture
    def mock_container(self):
        container = MagicMock()
        container.get_config_update_interactor.return_value = AsyncMock()
        return container

    @pytest.fixture
    def mock_console(self):
        return MagicMock()

    @pytest.fixture
    def config_update_use_case(self, mock_container, mock_console):
        return ConfigUpdateUseCase(mock_container, mock_console)

    @pytest.mark.asyncio
    async def test_it_validates_no_devices(self, config_update_use_case):
        request = DeviceConfigUpdateRequest()

        with pytest.raises(ValueError, match="No devices specified"):
            await config_update_use_case.execute(request)
