"""Tests for ExecuteComponentActionUseCase."""

from unittest.mock import AsyncMock

import pytest
from core.domain.value_objects.action_result import ActionResult
from core.domain.value_objects.component_action_request import ComponentActionRequest
from core.use_cases.execute_component_action import ExecuteComponentActionUseCase


class TestExecuteComponentActionUseCase:

    @pytest.fixture
    def use_case(self, mock_device_gateway):
        return ExecuteComponentActionUseCase(device_gateway=mock_device_gateway)

    async def test_it_executes_component_action_successfully(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        component_key = "Shelly"
        action = "Reboot"
        parameters = {}

        expected_result = ActionResult(
            device_ip=device_ip,
            action_type=f"{component_key}.{action}",
            success=True,
            message="Reboot executed successfully on Shelly",
        )
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=expected_result
        )

        request = ComponentActionRequest(
            device_ip=device_ip,
            component_key=component_key,
            action=action,
            parameters=parameters,
        )
        result = await use_case.execute(request)

        assert result.success is True
        assert result.device_ip == device_ip
        assert result.action_type == f"{component_key}.{action}"
        mock_device_gateway.execute_component_action.assert_called_once_with(
            device_ip, component_key, action, parameters
        )

    async def test_it_handles_component_action_failure(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        component_key = "switch:0"
        action = "Toggle"
        parameters = {}

        expected_result = ActionResult(
            device_ip=device_ip,
            action_type=f"{component_key}.{action}",
            success=False,
            message="Action not supported",
            error="Method Switch.Toggle not found in available methods",
        )
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=expected_result
        )

        request = ComponentActionRequest(
            device_ip=device_ip,
            component_key=component_key,
            action=action,
            parameters=parameters,
        )
        result = await use_case.execute(request)

        assert result.success is False
        assert result.error is not None
        mock_device_gateway.execute_component_action.assert_called_once_with(
            device_ip, component_key, action, parameters
        )

    async def test_it_executes_action_with_parameters(
        self, use_case, mock_device_gateway
    ):
        device_ip = "192.168.1.100"
        component_key = "Shelly"
        action = "Update"
        parameters = {"channel": "beta"}

        expected_result = ActionResult(
            device_ip=device_ip,
            action_type=f"{component_key}.{action}",
            success=True,
            message="Update executed successfully on Shelly",
            data={"update_initiated": True},
        )
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=expected_result
        )

        request = ComponentActionRequest(
            device_ip=device_ip,
            component_key=component_key,
            action=action,
            parameters=parameters,
        )
        result = await use_case.execute(request)

        assert result.success is True
        assert result.data is not None
        mock_device_gateway.execute_component_action.assert_called_once_with(
            device_ip, component_key, action, parameters
        )
