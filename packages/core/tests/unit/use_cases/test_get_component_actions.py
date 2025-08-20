"""Tests for GetComponentActionsUseCase."""

from unittest.mock import AsyncMock

import pytest
from core.domain.entities.device_status import DeviceStatus
from core.domain.value_objects.get_component_actions_request import (
    GetComponentActionsRequest,
)
from core.use_cases.get_component_actions import GetComponentActionsUseCase


class TestGetComponentActionsUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return GetComponentActionsUseCase(device_gateway=mock_device_gateway)

    async def test_it_gets_component_actions_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"

        from unittest.mock import MagicMock

        mock_component1 = MagicMock()
        mock_component1.key = "sys"
        mock_component1.available_actions = ["Sys.Reboot", "Shelly.Update"]

        mock_component2 = MagicMock()
        mock_component2.key = "switch:0"
        mock_component2.available_actions = ["Switch.Toggle", "Switch.Set"]

        mock_device_status = MagicMock()
        mock_device_status.components = [mock_component1, mock_component2]

        mock_device_gateway.get_device_status = AsyncMock(
            return_value=mock_device_status
        )

        request = GetComponentActionsRequest(device_ip=device_ip)
        result = await use_case.execute(request)

        expected_result = {
            "sys": ["Sys.Reboot", "Shelly.Update"],
            "switch:0": ["Switch.Toggle", "Switch.Set"],
        }
        assert result == expected_result
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_handles_device_not_found(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.200"
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        request = GetComponentActionsRequest(device_ip=device_ip)
        result = await use_case.execute(request)

        assert result == {}
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)

    async def test_it_handles_empty_components(self, use_case, mock_device_gateway):
        device_ip = "192.168.1.100"

        mock_device_status = DeviceStatus(
            device_ip=device_ip, components=[], available_methods=[]
        )
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=mock_device_status
        )

        request = GetComponentActionsRequest(device_ip=device_ip)
        result = await use_case.execute(request)

        assert result == {}
        mock_device_gateway.get_device_status.assert_called_once_with(device_ip)
