from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.domain.entities.device_status import DeviceStatus
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.entities.exceptions import (
    DeviceAuthenticationError,
    DeviceUnreachableError,
)
from core.domain.enums.enums import Status
from core.domain.value_objects.action_result import ActionResult
from core.gateways.device.legacy_device_gateway import LegacyDeviceGateway
from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway
from core.services.auth_state_cache import AuthStateCache


class TestShellyDeviceGateway:

    @pytest.fixture
    def mock_rpc_client(self):
        return MagicMock()

    @pytest.fixture
    def mock_legacy_gateway(self):
        return AsyncMock(spec=LegacyDeviceGateway)

    @pytest.fixture
    def gateway(self, mock_rpc_client, mock_legacy_gateway):
        return ShellyDeviceGateway(
            rpc_client=mock_rpc_client, legacy_gateway=mock_legacy_gateway
        )

    async def test_it_discovers_device_successfully(self, gateway, mock_rpc_client):
        device_info = {
            "id": "shelly1pm-001",
            "model": "SHPM-1",
            "app": "Plus1PM",
            "name": "Living Room Switch",
            "fw_id": "20230913-114010/v1.14.0-gcb84623",
        }
        update_info = {}

        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[(device_info, 0.15), (update_info, 0.05)]
        )

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.ip == "192.168.1.100"
        assert result.status == Status.NO_UPDATE_NEEDED
        assert result.device_id == "shelly1pm-001"
        assert result.device_type == "SHPM-1"
        assert result.app_name == "Plus1PM"
        assert result.device_name == "Living Room Switch"
        assert result.firmware_version == "20230913-114010/v1.14.0-gcb84623"
        assert result.response_time == 0.15
        assert isinstance(result.last_seen, datetime)
        assert mock_rpc_client.make_rpc_request.call_count == 2
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (
            ("192.168.1.100", "Shelly.GetDeviceInfo"),
            {"timeout": 10.0},
        )
        assert calls[1] == (
            ("192.168.1.100", "Shelly.CheckForUpdate"),
            {"timeout": 10.0},
        )

    async def test_it_discovers_device_with_custom_timeout(
        self, gateway, mock_rpc_client
    ):
        device_info = {"id": "test-device", "model": "SHSW-1", "fw_id": "1.0.0"}
        update_info = {}

        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[(device_info, 0.2), (update_info, 0.05)]
        )

        result = await gateway.discover_device("192.168.1.100", timeout=2.5)

        assert result is not None
        assert mock_rpc_client.make_rpc_request.call_count == 2
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (
            ("192.168.1.100", "Shelly.GetDeviceInfo"),
            {"timeout": 2.5},
        )
        assert calls[1] == (
            ("192.168.1.100", "Shelly.CheckForUpdate"),
            {"timeout": 2.5},
        )

    async def test_it_handles_device_discovery_failure(
        self, gateway, mock_rpc_client, mock_legacy_gateway
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=Exception("Network timeout")
        )
        mock_legacy_gateway.discover_device.return_value = None

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.ip == "192.168.1.100"
        assert result.status == Status.UNREACHABLE
        assert result.error_message == "Network timeout"
        assert isinstance(result.last_seen, datetime)

    async def test_it_gets_device_status_with_updates(self, gateway, mock_rpc_client):
        components_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {
                        "mac": "AABBCCDDEEFF",
                        "restart_required": False,
                        "uptime": 3600,
                        "available_updates": {"version": "1.1.0"},
                    },
                    "config": {
                        "device": {
                            "name": "Test Device",
                            "fw_id": "20240101-120000/1.0.0-abcd123",
                        }
                    },
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"name": "Test Device", "model": "SHPM-1"}, 0.05),
                (components_data, 0.1),
                ({"sys": {"mac": "AABBCCDDEEFF", "restart_required": False}}, 0.1),
                (["Sys.Reboot", "Sys.Update"], 0.05),
            ]
        )

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert len(result.components) == 1
        assert result.total_components == 1
        assert mock_rpc_client.make_rpc_request.call_count == 4
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.GetComponents", params={"offset": 0}, timeout=10.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.GetStatus", timeout=10.0
        )

    async def test_it_gets_device_status_without_updates(
        self, gateway, mock_rpc_client
    ):
        components_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {
                        "mac": "AABBCCDDEEFF",
                        "restart_required": False,
                        "uptime": 3600,
                    },
                    "config": {
                        "device": {
                            "name": "Test Device",
                            "fw_id": "20240101-120000/1.0.0-abcd123",
                        }
                    },
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"name": "Test Device", "model": "SHPM-1"}, 0.05),
                (components_data, 0.1),
                ({"sys": {"mac": "AABBCCDDEEFF", "restart_required": False}}, 0.1),
                (["Sys.Reboot", "Sys.GetConfig"], 0.05),
            ]
        )

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert mock_rpc_client.make_rpc_request.call_count == 4
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.GetComponents", params={"offset": 0}, timeout=10.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.GetStatus", timeout=10.0
        )

    async def test_it_gets_device_status_with_zigbee_data(
        self, gateway, mock_rpc_client
    ):
        components_data = {
            "components": [
                {
                    "key": "switch:0",
                    "status": {"output": True},
                    "config": {"name": "Test Switch"},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }
        zigbee_data = {"network_state": "joined"}

        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"name": "Test Device", "model": "SHPM-1"}, 0.05),
                (components_data, 0.1),
                ({"zigbee": zigbee_data}, 0.1),
                (["Switch.Set"], 0.05),
            ]
        )

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert len(result.components) == 2

        assert mock_rpc_client.make_rpc_request.call_count == 4
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (
            ("192.168.1.100", "Shelly.GetDeviceInfo"),
            {"timeout": 10.0},
        )
        assert calls[1] == (
            ("192.168.1.100", "Shelly.GetComponents"),
            {"params": {"offset": 0}, "timeout": 10.0},
        )
        assert calls[2] == (("192.168.1.100", "Shelly.GetStatus"), {"timeout": 10.0})
        assert calls[3] == (("192.168.1.100", "Shelly.ListMethods"), {"timeout": 10.0})

    async def test_it_gets_device_status_with_zigbee_failure(
        self, gateway, mock_rpc_client
    ):
        components_data = {
            "components": [
                {
                    "key": "switch:0",
                    "status": {"output": True},
                    "config": {"name": "Test Switch"},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            ({"name": "Test Device", "model": "SHPM-1"}, 0.05),
            (components_data, 0.1),
            Exception("Status not available"),
            (["Switch.Set"], 0.05),
        ]

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert len(result.components) == 1

        assert mock_rpc_client.make_rpc_request.call_count == 4
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (
            ("192.168.1.100", "Shelly.GetDeviceInfo"),
            {"timeout": 10.0},
        )
        assert calls[1] == (
            ("192.168.1.100", "Shelly.GetComponents"),
            {"params": {"offset": 0}, "timeout": 10.0},
        )
        assert calls[2] == (("192.168.1.100", "Shelly.GetStatus"), {"timeout": 10.0})
        assert calls[3] == (("192.168.1.100", "Shelly.ListMethods"), {"timeout": 10.0})

    async def test_it_returns_the_rpc_payload_not_the_response_frame(
        self, gateway, mock_rpc_client
    ):
        # Frame captured verbatim from a Gen4 device: the config a caller wants
        # sits under "result", alongside the request id and the device id.
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": ["Switch.GetConfig"]}, 0.1),
                (
                    {
                        "id": "68ef3f1a-b13a-490b-9ab0-d4b8f21d5580",
                        "src": "shelly1pmminig4-7c2c676d30d4",
                        "result": {"id": 0, "name": None, "in_mode": "flip"},
                    },
                    0.1,
                ),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "GetConfig"
        )

        assert result.success is True
        assert result.data == {"id": 0, "name": None, "in_mode": "flip"}

    async def test_it_reports_a_device_rejection_as_a_failed_action(
        self, gateway, mock_rpc_client
    ):
        # Devices answer a rejected call with HTTP 200 and an "error" member,
        # so a frame that is never opened reads as a success.
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": ["Switch.GetConfig"]}, 0.1),
                (
                    {
                        "id": "b036bb7f-91f8-4b4b-b81b-0376cafedee0",
                        "src": "shelly1pmminig4-7c2c676d30d4",
                        "error": {
                            "code": -105,
                            "message": "Argument 'id', value 99 not found!",
                        },
                    },
                    0.1,
                ),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:99", "GetConfig"
        )

        assert result.success is False
        assert result.data is None
        assert "value 99 not found" in result.error
        assert "-105" in result.error

    async def test_it_handles_update_check_failure_gracefully(
        self, gateway, mock_rpc_client
    ):
        device_info = {"id": "test-device", "model": "SHSW-1", "fw_id": "1.0.0"}
        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            (device_info, 0.1),
            Exception("Update check failed"),
        ]

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None

        assert result.status == Status.DETECTED

    async def test_it_detects_auth_required_from_auth_en(
        self, mock_rpc_client, mock_legacy_gateway
    ):
        auth_state_cache = MagicMock()
        auth_state_cache.requires_auth.return_value = False
        gateway = ShellyDeviceGateway(
            rpc_client=mock_rpc_client,
            legacy_gateway=mock_legacy_gateway,
            auth_state_cache=auth_state_cache,
        )

        device_info = {
            "id": "ShellyWallDisplay-000822891495",
            "model": "SAWD-0A1XX10EU1",
            "fw_id": "20260313-152112/2.5.8-4ec844c8",
            "auth_en": True,
        }
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                (device_info, 0.1),
                Exception("Auth required for update check"),
            ]
        )

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.auth_required is True
        auth_state_cache.mark_auth_required.assert_called_once()

    async def test_it_keeps_update_status_when_auth_succeeds(
        self, mock_rpc_client, mock_legacy_gateway
    ):
        auth_state_cache = MagicMock()
        auth_state_cache.requires_auth.return_value = False
        gateway = ShellyDeviceGateway(
            rpc_client=mock_rpc_client,
            legacy_gateway=mock_legacy_gateway,
            auth_state_cache=auth_state_cache,
        )

        device_info = {
            "id": "ShellyWallDisplay-000822891495",
            "model": "SAWD-0A1XX10EU1",
            "fw_id": "20260313-152112/2.5.8-4ec844c8",
            "auth_en": True,
        }
        update_info = {"stable": {"version": "2.6.0"}}
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[(device_info, 0.1), (update_info, 0.05)]
        )

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.auth_required is True
        assert result.status == Status.UPDATE_AVAILABLE

    async def test_it_propagates_auth_error_from_get_device_status(
        self, mock_rpc_client, mock_legacy_gateway
    ):
        gateway = ShellyDeviceGateway(
            rpc_client=mock_rpc_client, legacy_gateway=mock_legacy_gateway
        )

        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"name": "Test", "model": "SAWD-0A1XX10EU1"}, 0.05),
                DeviceAuthenticationError("192.168.1.100", "No credentials stored"),
                ({"sys": {}}, 0.1),
                ({"methods": []}, 0.05),
            ]
        )

        with pytest.raises(DeviceAuthenticationError):
            await gateway.get_device_status("192.168.1.100")

    async def test_it_marks_auth_required_while_the_cache_is_still_empty(
        self, mock_rpc_client, mock_legacy_gateway
    ):
        auth_state_cache = AuthStateCache()
        gateway = ShellyDeviceGateway(
            rpc_client=mock_rpc_client,
            legacy_gateway=mock_legacy_gateway,
            auth_state_cache=auth_state_cache,
        )
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"id": "shelly1-abc", "auth_en": True}, 0.1),
                ({}, 0.05),
            ]
        )

        result = await gateway.discover_device("192.168.1.100")

        assert result.auth_required is True
        assert auth_state_cache.requires_auth("192.168.1.100") is True

    async def test_it_marks_auth_required_from_a_status_read_on_an_empty_cache(
        self, mock_rpc_client, mock_legacy_gateway
    ):
        auth_state_cache = AuthStateCache()
        gateway = ShellyDeviceGateway(
            rpc_client=mock_rpc_client,
            legacy_gateway=mock_legacy_gateway,
            auth_state_cache=auth_state_cache,
        )
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"auth_en": True}, 0.05),
                ({"components": [], "cfg_rev": 1, "total": 0}, 0.1),
                ({"sys": {}}, 0.1),
                ({"methods": []}, 0.05),
            ]
        )

        await gateway.get_device_status("192.168.1.100")

        assert auth_state_cache.requires_auth("192.168.1.100") is True

    async def test_it_marks_auth_required_before_a_later_read_can_fail(
        self, mock_rpc_client, mock_legacy_gateway
    ):
        auth_state_cache = MagicMock()
        gateway = ShellyDeviceGateway(
            rpc_client=mock_rpc_client,
            legacy_gateway=mock_legacy_gateway,
            auth_state_cache=auth_state_cache,
        )
        mock_legacy_gateway.get_device_status.return_value = None
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"auth_en": True}, 0.1),
                (None, 0.1),
                ({}, 0.1),
                ({"methods": []}, 0.05),
            ]
        )

        await gateway.get_device_status("192.168.1.100")

        auth_state_cache.mark_auth_required.assert_called_once()

    async def test_it_does_not_propagate_an_auth_error_from_device_info_alone(
        self, gateway, mock_rpc_client
    ):
        components_data = {"components": [], "cfg_rev": 1, "total": 0}
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                DeviceAuthenticationError("192.168.1.100", "No credentials stored"),
                (components_data, 0.1),
                ({"sys": {}}, 0.1),
                ({"methods": ["Switch.Toggle"]}, 0.05),
            ]
        )

        result = await gateway.get_device_status("192.168.1.100")

        assert isinstance(result, DeviceStatus)
        assert result.device_name is None

    async def test_it_continues_on_generic_error_in_get_device_status(
        self, gateway, mock_rpc_client
    ):
        components_data = {
            "components": [],
            "cfg_rev": 1,
            "total": 0,
        }
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"name": "Test", "model": "SHPM-1"}, 0.05),
                (components_data, 0.1),
                Exception("Status temporarily unavailable"),
                ({"methods": []}, 0.05),
            ]
        )

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)

    async def test_it_executes_component_update_action_successfully(
        self, gateway, mock_rpc_client
    ):

        available_methods = ["Shelly.Update", "Shelly.Reboot", "Switch.Toggle"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": available_methods}, 0.1),
                ({}, 0.1),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "shelly", "Update"
        )

        assert result.success is True
        assert result.action_type == "shelly.Update"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Update executed successfully on shelly"
        assert mock_rpc_client.make_rpc_request.call_count == 2
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.ListMethods", timeout=10.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.Update", params=None, timeout=10.0
        )

    async def test_it_forwards_the_stage_to_the_update_action(
        self, gateway, mock_rpc_client
    ):

        available_methods = ["Shelly.Update", "Shelly.Reboot", "Switch.Toggle"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": available_methods}, 0.1),
                ({}, 0.1),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "shelly", "Update", {"stage": "beta"}
        )

        assert result.success is True
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.Update", params={"stage": "beta"}, timeout=10.0
        )

    async def test_it_executes_component_reboot_action_successfully(
        self, gateway, mock_rpc_client
    ):

        available_methods = ["Shelly.Update", "Shelly.Reboot", "Switch.Toggle"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": available_methods}, 0.1),
                ({}, 0.1),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "shelly", "Reboot"
        )

        assert result.success is True
        assert result.action_type == "shelly.Reboot"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Reboot executed successfully on shelly"
        assert mock_rpc_client.make_rpc_request.call_count == 2
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.ListMethods", timeout=10.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.Reboot", params=None, timeout=10.0
        )

    async def test_it_executes_component_config_get_action_successfully(
        self, gateway, mock_rpc_client
    ):
        config_data = {"wifi": {"ssid": "TestNetwork"}, "name": "Test Device"}

        available_methods = ["Sys.GetConfig", "Sys.SetConfig", "Sys.Reboot"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": available_methods}, 0.1),
                (config_data, 0.1),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "sys", "GetConfig"
        )

        assert result.success is True
        assert result.action_type == "sys.GetConfig"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "GetConfig executed successfully on sys"
        assert result.data == config_data
        assert mock_rpc_client.make_rpc_request.call_count == 2
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.ListMethods", timeout=10.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Sys.GetConfig", params=None, timeout=10.0
        )

    async def test_it_executes_component_config_set_action_successfully(
        self, gateway, mock_rpc_client
    ):

        available_methods = ["Sys.GetConfig", "Sys.SetConfig", "Sys.Reboot"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                (available_methods, 0.1),
                ({}, 0.1),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "sys", "SetConfig"
        )

        assert result.success is True
        assert result.action_type == "sys.SetConfig"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "SetConfig executed successfully on sys"
        assert mock_rpc_client.make_rpc_request.call_count == 2
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.ListMethods", timeout=10.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Sys.SetConfig", params=None, timeout=10.0
        )

    async def test_it_handles_component_action_validation_failure(
        self, gateway, mock_rpc_client
    ):

        available_methods = ["Sys.GetConfig", "Sys.Reboot"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=({"methods": available_methods}, 0.1)
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "sys", "SetConfig"
        )

        assert result.success is False
        assert result.action_type == "sys.SetConfig"
        assert "has no method" in result.error
        assert mock_rpc_client.make_rpc_request.call_count == 1

    async def test_it_handles_component_action_with_invalid_component(
        self, gateway, mock_rpc_client
    ):

        available_methods = ["Sys.GetConfig", "Sys.Reboot", "Switch.Toggle"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=({"methods": available_methods}, 0.1)
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "invalid_component", "SomeAction"
        )

        assert result.success is False
        assert result.action_type == "invalid_component.SomeAction"
        assert "has no method" in result.error
        assert mock_rpc_client.make_rpc_request.call_count == 1

    async def test_it_handles_component_action_execution_failure(
        self, gateway, mock_rpc_client
    ):

        available_methods = ["Sys.Reboot", "Shelly.Update"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                (available_methods, 0.1),
                Exception("RPC call failed"),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "sys", "Reboot"
        )

        assert result.success is False
        assert result.action_type == "sys.Reboot"
        assert "RPC call failed" in result.error

    async def test_it_executes_bulk_actions_successfully(
        self, gateway, mock_rpc_client
    ):
        device_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]

        available_methods = ["Shelly.Reboot", "Shelly.Update", "Shelly.FactoryReset"]
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": available_methods}, 0.1),
                ({"methods": available_methods}, 0.1),
                ({"methods": available_methods}, 0.1),
                ({}, 0.1),
                ({}, 0.1),
                ({}, 0.1),
            ]
        )

        results = await gateway.execute_bulk_action(device_ips, "shelly", "Reboot")

        assert len(results) == 3
        assert all(result.success for result in results)
        assert all(result.action_type == "shelly.Reboot" for result in results)
        assert mock_rpc_client.make_rpc_request.call_count == 6

    async def test_it_rejects_bulk_action_with_unsupported_action(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock()

        with pytest.raises(ValueError, match="not supported"):
            await gateway.execute_bulk_action(
                ["192.168.1.100"], "shelly", "AnythingAtAll"
            )

        mock_rpc_client.make_rpc_request.assert_not_called()

    async def test_it_rejects_bulk_action_with_unsupported_component(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock()

        with pytest.raises(ValueError, match="not supported"):
            await gateway.execute_bulk_action(["192.168.1.100"], "switch:0", "Update")

        mock_rpc_client.make_rpc_request.assert_not_called()

    async def test_it_handles_device_with_partial_info(self, gateway, mock_rpc_client):
        device_info = {"id": "minimal-device"}
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=(device_info, 0.1))

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.device_id == "minimal-device"
        assert result.device_type is None
        assert result.device_name is None
        assert result.firmware_version is None

    async def test_it_handles_empty_device_info(self, gateway, mock_rpc_client):
        device_info = {}
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=(device_info, 0.1))

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.device_id is None
        assert result.device_type is None

    async def test_it_handles_update_info_without_versions(
        self, gateway, mock_rpc_client
    ):
        device_info = {"id": "test-device", "model": "SHSW-1", "fw_id": "1.0.0"}
        update_info = {"stable": {}, "beta": {}}
        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            (device_info, 0.1),
            (update_info, 0.05),
        ]

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.status == Status.NO_UPDATE_NEEDED

    async def test_it_handles_null_update_info(self, gateway, mock_rpc_client):
        device_info = {"id": "test-device", "model": "SHSW-1", "fw_id": "1.0.0"}
        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            (device_info, 0.1),
            (None, 0.05),
        ]

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.status == Status.DETECTED

    async def test_it_includes_device_info_data_in_device_status(
        self, gateway, mock_rpc_client
    ):
        device_info_data = {
            "name": "Fresh Device Name",
            "model": "SNSW-001X16EU",
            "fw_id": "20231026-112640/v1.14.1-ga898e3a",
            "mac": "AA:BB:CC:DD:EE:FF",
            "app": "switch",
        }
        components_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {"device_name": "Old Name"},
                    "config": {"device": {"name": "Config Name"}},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            (device_info_data, 0.1),
            (components_data, 0.1),
            ({"sys": {"mac": "AA:BB:CC:DD:EE:FF"}}, 0.1),
            (["Switch.Set", "Component.GetConfig"], 0.05),
        ]

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)

        assert result.device_name == "Fresh Device Name"
        assert result.device_type == "SNSW-001X16EU"
        assert result.firmware_version == "20231026-112640/v1.14.1-ga898e3a"
        assert result.mac_address == "AA:BB:CC:DD:EE:FF"
        assert result.app_name == "switch"

        assert mock_rpc_client.make_rpc_request.call_count == 4
        calls = mock_rpc_client.make_rpc_request.call_args_list

        assert calls[0] == (
            ("192.168.1.100", "Shelly.GetDeviceInfo"),
            {"timeout": 10.0},
        )

        assert calls[1] == (
            ("192.168.1.100", "Shelly.GetComponents"),
            {"params": {"offset": 0}, "timeout": 10.0},
        )

    async def test_it_handles_device_info_failure_gracefully(
        self, gateway, mock_rpc_client
    ):
        components_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {"device_name": "Fallback Name"},
                    "config": {},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            Exception("GetDeviceInfo failed"),
            (components_data, 0.1),
            Exception("Zigbee not available"),
            (["Switch.Set"], 0.05),
        ]

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)

        assert result.device_name is None
        assert result.device_type is None
        assert result.firmware_version is None
        assert result.mac_address is None
        assert result.app_name is None

        assert len(result.components) == 1

    async def test_it_handles_empty_device_info_response(
        self, gateway, mock_rpc_client
    ):
        device_info_data = {}
        components_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {"device_name": "Sys Name"},
                    "config": {},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            (device_info_data, 0.1),
            (components_data, 0.1),
            Exception("Zigbee not available"),
            (["Switch.Set"], 0.05),
        ]

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None

        assert result.device_name is None
        assert result.device_type is None
        assert result.firmware_version is None
        assert result.mac_address is None
        assert result.app_name is None

    async def test_it_handles_partial_device_info_data(self, gateway, mock_rpc_client):
        device_info_data = {
            "name": "Partial Device Name",
            "model": "SNSW-001X16EU",
        }
        components_data = {
            "components": [
                {
                    "key": "sys",
                    "status": {},
                    "config": {},
                    "attrs": {},
                }
            ],
            "cfg_rev": 1,
            "total": 1,
        }

        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            (device_info_data, 0.1),
            (components_data, 0.1),
            Exception("Zigbee not available"),
            (["Switch.Set"], 0.05),
        ]

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None

        assert result.device_name == "Partial Device Name"
        assert result.device_type == "SNSW-001X16EU"

        assert result.firmware_version is None
        assert result.mac_address is None
        assert result.app_name is None

    async def test_it_continues_on_component_failure(self, gateway, mock_rpc_client):
        device_info_data = {
            "name": "Test Device",
            "model": "SNSW-001X16EU",
        }

        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            (device_info_data, 0.1),
            Exception("GetComponents failed"),
        ]

        result = await gateway.get_device_status("192.168.1.100")

        assert isinstance(result, DeviceStatus)

        assert result.device_name == "Test Device"
        assert result.device_type == "SNSW-001X16EU"
        assert result.firmware_version is None
        assert result.mac_address is None
        assert result.app_name is None
        assert len(result.components) == 0

        assert mock_rpc_client.make_rpc_request.call_count == 4
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (
            ("192.168.1.100", "Shelly.GetDeviceInfo"),
            {"timeout": 10.0},
        )


class TestActionNameResolution:

    DEVICE_METHODS = [
        "Switch.Toggle",
        "Shelly.Reboot",
        "Wifi.SetConfig",
        "Mqtt.SetConfig",
        "EMData.GetStatus",
        "EM1Data.GetStatus",
    ]

    @pytest.fixture
    def mock_rpc_client(self):
        return MagicMock()

    @pytest.fixture
    def gateway(self, mock_rpc_client):
        return ShellyDeviceGateway(
            rpc_client=mock_rpc_client,
            legacy_gateway=AsyncMock(spec=LegacyDeviceGateway),
        )

    @pytest.fixture
    def listing_device(self, mock_rpc_client):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": self.DEVICE_METHODS}, 0.1),
                ({}, 0.1),
            ]
        )
        return mock_rpc_client

    @pytest.mark.parametrize(
        "component_key,action,expected_method,expected_params",
        [
            ("emdata:0", "GetStatus", "EMData.GetStatus", {"id": 0}),
            ("emdata:0", "EMData.GetStatus", "EMData.GetStatus", {"id": 0}),
            ("em1data:1", "GetStatus", "EM1Data.GetStatus", {"id": 1}),
            ("switch:0", "Switch.Toggle", "Switch.Toggle", {"id": 0}),
            ("switch:0", "Toggle", "Switch.Toggle", {"id": 0}),
            ("sys", "Shelly.Reboot", "Shelly.Reboot", None),
            ("wifi", "SetConfig", "Wifi.SetConfig", None),
            ("wifi", "WiFi.SetConfig", "Wifi.SetConfig", None),
            ("mqtt", "SetConfig", "Mqtt.SetConfig", None),
            ("mqtt", "MQTT.SetConfig", "Mqtt.SetConfig", None),
        ],
    )
    async def test_it_sends_the_method_name_the_device_reported(
        self,
        gateway,
        listing_device,
        component_key,
        action,
        expected_method,
        expected_params,
    ):
        result = await gateway.execute_component_action(
            "192.168.1.100", component_key, action
        )

        assert result.success is True
        listing_device.make_rpc_request.assert_any_call(
            "192.168.1.100", expected_method, params=expected_params, timeout=10.0
        )

    async def test_it_rejects_a_method_the_device_does_not_report(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=({"methods": self.DEVICE_METHODS}, 0.1)
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "Switch.Nonsense"
        )

        assert result.success is False
        assert "Switch.Nonsense not supported by switch:0" in result.message

    async def test_it_sends_the_qualified_name_when_the_device_lists_nothing(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": []}, 0.1),
                ({}, 0.1),
            ]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "Toggle"
        )

        assert result.success is True
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Switch.Toggle", params={"id": 0}, timeout=10.0
        )

    @pytest.mark.parametrize("action", ["Reboot", "Shelly.Reboot"])
    async def test_it_accepts_bulk_actions_bare_or_qualified(
        self, gateway, mock_rpc_client, action
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": self.DEVICE_METHODS}, 0.1),
                ({}, 0.1),
            ]
        )

        results = await gateway.execute_bulk_action(["192.168.1.100"], "shelly", action)

        assert [r.success for r in results] == [True]

    @pytest.mark.parametrize(
        "component_key,action",
        [
            ("shelly", "Switch.Toggle"),
            ("shelly", "Nonsense"),
            ("switch:0", "Reboot"),
            ("switch:0", "Shelly.Reboot"),
        ],
    )
    async def test_it_still_refuses_bulk_actions_outside_the_allowlist(
        self, gateway, component_key, action
    ):
        with pytest.raises(ValueError):
            await gateway.execute_bulk_action(["192.168.1.100"], component_key, action)

    @pytest.mark.parametrize("action", ["Toggle", "Switch.Toggle"])
    async def test_it_reports_the_same_action_type_bare_or_qualified(
        self, gateway, listing_device, action
    ):
        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", action
        )

        assert result.action_type == "switch:0.Toggle"
        assert result.message == "Toggle executed successfully on switch:0"


class TestComponentOwnershipOnExecute:

    DEVICE_METHODS = [
        "Switch.Toggle",
        "Wifi.SetConfig",
        "Zigbee.GetStatus",
        "Shelly.ZigbeeClear",
        "Sys.GetConfig",
        "Shelly.Reboot",
        "Shelly.FactoryReset",
    ]

    @pytest.fixture
    def mock_rpc_client(self):
        return MagicMock()

    @pytest.fixture
    def gateway(self, mock_rpc_client):
        return ShellyDeviceGateway(
            rpc_client=mock_rpc_client,
            legacy_gateway=AsyncMock(spec=LegacyDeviceGateway),
        )

    @pytest.mark.parametrize(
        "component_key,action",
        [
            ("wifi", "Shelly.FactoryReset"),
            ("switch:0", "Shelly.FactoryReset"),
            ("zigbee", "FactoryReset"),
            ("zigbee", "Shelly.FactoryReset"),
            ("mqtt", "Switch.Toggle"),
        ],
    )
    async def test_it_never_sends_a_method_the_component_does_not_own(
        self, gateway, mock_rpc_client, component_key, action
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=({"methods": self.DEVICE_METHODS}, 0.1)
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", component_key, action
        )

        assert result.success is False
        sent = [c.args[1] for c in mock_rpc_client.make_rpc_request.call_args_list]
        assert sent == ["Shelly.ListMethods"]

    async def test_it_still_reaches_a_shelly_method_the_sys_component_owns(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[({"methods": self.DEVICE_METHODS}, 0.1), ({}, 0.1)]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "sys", "Reboot"
        )

        assert result.success is True
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.Reboot", params=None, timeout=10.0
        )

    async def test_it_still_reaches_the_shelly_method_zigbee_owns(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[({"methods": self.DEVICE_METHODS}, 0.1), ({}, 0.1)]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "zigbee", "ZigbeeClear"
        )

        assert result.success is True
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.ZigbeeClear", params=None, timeout=10.0
        )

    @pytest.mark.parametrize("action", ["Shelly.FactoryReset", "shelly.factoryreset"])
    async def test_it_refuses_an_unowned_call_when_list_methods_fails(
        self, gateway, mock_rpc_client, action
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[Exception("ListMethods timed out"), ({}, 0.1)]
        )

        result = await gateway.execute_component_action("192.168.1.100", "wifi", action)

        assert result.success is False
        sent = [c.args[1] for c in mock_rpc_client.make_rpc_request.call_args_list]
        assert sent == ["Shelly.ListMethods"]

    async def test_it_still_runs_a_bare_action_when_list_methods_fails(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[Exception("ListMethods timed out"), ({}, 0.1)]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "wifi", "SetConfig"
        )

        assert result.success is True
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Wifi.SetConfig", params=None, timeout=10.0
        )


class TestUnreadableMethodLists:

    @pytest.fixture
    def mock_rpc_client(self):
        return MagicMock()

    @pytest.fixture
    def gateway(self, mock_rpc_client):
        return ShellyDeviceGateway(rpc_client=mock_rpc_client)

    @pytest.mark.parametrize(
        "payload,expected",
        [
            ({"methods": ["Switch.Toggle", None, 7]}, ["Switch.Toggle"]),
            ({"methods": [None]}, []),
            ({"methods": "Switch.Toggle"}, []),
            ({"unexpected": []}, []),
            ({}, []),
        ],
    )
    async def test_it_keeps_only_the_entries_that_are_method_names(
        self, gateway, mock_rpc_client, payload, expected
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=(payload, 0.1))

        assert await gateway._get_available_methods("192.168.1.100") == expected

    async def test_it_does_not_break_execution_on_a_list_of_non_names(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[({"methods": [None]}, 0.1), ({}, 0.1)]
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "Toggle"
        )

        assert result.success is True
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Switch.Toggle", params={"id": 0}, timeout=10.0
        )


class TestBulkAllowlistCasing:

    @pytest.fixture
    def mock_rpc_client(self):
        return MagicMock()

    @pytest.fixture
    def gateway(self, mock_rpc_client):
        return ShellyDeviceGateway(rpc_client=mock_rpc_client)

    @pytest.mark.parametrize(
        "component_key,action",
        [
            ("shelly", "Reboot"),
            ("shelly", "Shelly.Reboot"),
            ("shelly", "shelly.Reboot"),
            ("SHELLY", "Shelly.reboot"),
            ("shelly", "SHELLY.REBOOT"),
        ],
    )
    async def test_it_accepts_the_allowlisted_action_however_it_is_spelled(
        self, gateway, mock_rpc_client, component_key, action
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[({"methods": ["Shelly.Reboot"]}, 0.1), ({}, 0.1)]
        )

        results = await gateway.execute_bulk_action(
            ["192.168.1.100"], component_key, action
        )

        assert [r.success for r in results] == [True]
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.Reboot", params=None, timeout=10.0
        )

    @pytest.mark.parametrize(
        "component_key,action",
        [
            ("shelly", "Switch.Toggle"),
            ("shelly", "Nonsense"),
            ("switch:0", "Reboot"),
            ("switch:0", "Shelly.Reboot"),
        ],
    )
    async def test_it_still_refuses_anything_outside_the_allowlist(
        self, gateway, component_key, action
    ):
        with pytest.raises(ValueError):
            await gateway.execute_bulk_action(["192.168.1.100"], component_key, action)


class TestLegacyRouting:
    """The one seam between the RPC path and the Gen1 HTTP path."""

    @pytest.fixture
    def mock_rpc_client(self):
        return MagicMock()

    @pytest.fixture
    def mock_legacy_gateway(self):
        return AsyncMock(spec=LegacyDeviceGateway)

    @pytest.fixture
    def gateway(self, mock_rpc_client, mock_legacy_gateway):
        return ShellyDeviceGateway(
            rpc_client=mock_rpc_client, legacy_gateway=mock_legacy_gateway
        )

    @pytest.fixture
    def rpc_only_gateway(self, mock_rpc_client):
        return ShellyDeviceGateway(rpc_client=mock_rpc_client)

    async def test_it_discovers_over_the_legacy_path_when_rpc_fails(
        self, gateway, mock_rpc_client, mock_legacy_gateway
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(side_effect=Exception("RPC fail"))
        legacy_device = DiscoveredDevice(
            ip="192.168.1.200",
            status=Status.UPDATE_AVAILABLE,
            device_id="legacy-001",
            device_type="SHSW-1",
            last_seen=datetime.now(),
            has_update=True,
        )
        mock_legacy_gateway.discover_device.return_value = legacy_device

        result = await gateway.discover_device("192.168.1.200")

        assert result is legacy_device
        mock_legacy_gateway.discover_device.assert_awaited_once_with(
            "192.168.1.200", timeout=10.0
        )

    async def test_it_skips_the_legacy_path_when_the_host_is_unreachable(
        self, gateway, mock_rpc_client, mock_legacy_gateway
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=DeviceUnreachableError("192.168.1.250", "connect timeout")
        )

        result = await gateway.discover_device("192.168.1.250")

        assert result.status == Status.UNREACHABLE
        mock_legacy_gateway.discover_device.assert_not_called()

    async def test_it_forwards_the_timeout_to_both_paths(
        self, gateway, mock_rpc_client, mock_legacy_gateway
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(side_effect=Exception("RPC fail"))
        mock_legacy_gateway.discover_device.return_value = None

        await gateway.discover_device("192.168.1.42", timeout=2.5)

        assert mock_rpc_client.make_rpc_request.call_args_list[0] == (
            ("192.168.1.42", "Shelly.GetDeviceInfo"),
            {"timeout": 2.5},
        )
        mock_legacy_gateway.discover_device.assert_awaited_once_with(
            "192.168.1.42", timeout=2.5
        )

    async def test_it_reads_status_over_the_legacy_path_when_no_read_answers(
        self, gateway, mock_rpc_client, mock_legacy_gateway
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(side_effect=Exception("RPC fail"))
        legacy_status = DeviceStatus(
            device_ip="192.168.1.200",
            components=[],
            total_components=0,
            device_name="Legacy Switch",
        )
        mock_legacy_gateway.get_device_status.return_value = legacy_status

        result = await gateway.get_device_status("192.168.1.200")

        assert result is legacy_status
        mock_legacy_gateway.get_device_status.assert_awaited_once_with("192.168.1.200")

    async def test_it_keeps_the_rpc_status_when_a_single_read_answers(
        self, gateway, mock_rpc_client, mock_legacy_gateway
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                Exception("no device info"),
                ({"components": [], "cfg_rev": 1, "total": 0}, 0.1),
                Exception("no status"),
                Exception("no methods"),
            ]
        )

        result = await gateway.get_device_status("192.168.1.100")

        assert isinstance(result, DeviceStatus)
        mock_legacy_gateway.get_device_status.assert_not_called()

    @pytest.mark.parametrize(
        "component_key,action,success",
        [
            ("switch:0", "Legacy.Toggle", True),
            ("input:0", "Legacy.InputMomentary", True),
            ("wifi", "Legacy.SetConfig", True),
            ("wifi", "Legacy.Toggle", False),
        ],
    )
    async def test_it_hands_a_legacy_action_to_the_legacy_gateway_untouched(
        self,
        gateway,
        mock_rpc_client,
        mock_legacy_gateway,
        component_key,
        action,
        success,
    ):
        mock_rpc_client.make_rpc_request = AsyncMock()
        expected = ActionResult(
            device_ip="192.168.1.200",
            action_type=f"{component_key}.{action}",
            success=success,
            message="done" if success else f"Legacy action {action} not supported",
            error=None if success else "Unsupported legacy action",
        )
        mock_legacy_gateway.execute_action.return_value = expected

        result = await gateway.execute_component_action(
            "192.168.1.200", component_key, action
        )

        assert result is expected
        mock_legacy_gateway.execute_action.assert_awaited_once_with(
            "192.168.1.200", component_key, action, {}
        )
        mock_rpc_client.make_rpc_request.assert_not_called()

    async def test_it_reads_legacy_settings_through_the_route(
        self, gateway, mock_legacy_gateway
    ):
        mock_legacy_gateway.fetch_settings.return_value = {"name": "Gen1"}

        assert await gateway.get_legacy_settings("192.168.1.200") == {"name": "Gen1"}

    async def test_it_invalidates_legacy_credentials_through_the_route(
        self, gateway, mock_legacy_gateway
    ):
        gateway.invalidate_legacy_credential_cache("AA:BB:CC:DD:EE:FF")

        mock_legacy_gateway.invalidate_credential_cache.assert_called_once_with(
            "AA:BB:CC:DD:EE:FF"
        )

    async def test_it_reports_unreachable_when_there_is_no_legacy_path(
        self, rpc_only_gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(side_effect=Exception("RPC fail"))

        result = await rpc_only_gateway.discover_device("192.168.1.200")

        assert result.status == Status.UNREACHABLE
        assert result.error_message == "RPC fail"

    async def test_it_has_no_status_when_there_is_no_legacy_path(
        self, rpc_only_gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(side_effect=Exception("RPC fail"))

        assert await rpc_only_gateway.get_device_status("192.168.1.200") is None

    async def test_it_refuses_a_legacy_action_when_there_is_no_legacy_path(
        self, rpc_only_gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock()

        result = await rpc_only_gateway.execute_component_action(
            "192.168.1.200", "switch:0", "Legacy.Toggle"
        )

        assert result.success is False
        assert result.action_type == "switch:0.Legacy.Toggle"
        assert result.message == "Legacy gateway not available"
        assert result.error == "Legacy operations require legacy gateway injection"
        mock_rpc_client.make_rpc_request.assert_not_called()

    async def test_it_has_no_legacy_settings_when_there_is_no_legacy_path(
        self, rpc_only_gateway
    ):
        assert await rpc_only_gateway.get_legacy_settings("192.168.1.200") is None

    async def test_it_invalidates_nothing_when_there_is_no_legacy_path(
        self, rpc_only_gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock()

        rpc_only_gateway.invalidate_legacy_credential_cache("AA:BB:CC:DD:EE:FF")

        mock_rpc_client.make_rpc_request.assert_not_called()


class TestMethodListReuse:

    STATUS_READS = [
        ({"name": "Test Device"}, 0.05),
        ({"components": [], "cfg_rev": 1, "total": 0}, 0.1),
        ({"sys": {}}, 0.1),
        ({"methods": ["Switch.Toggle"]}, 0.05),
    ]

    @pytest.fixture
    def mock_rpc_client(self):
        return MagicMock()

    @pytest.fixture
    def gateway(self, mock_rpc_client):
        return ShellyDeviceGateway(rpc_client=mock_rpc_client)

    @staticmethod
    def _methods_sent(mock_rpc_client):
        return [c.args[1] for c in mock_rpc_client.make_rpc_request.call_args_list]

    async def test_it_asks_a_device_for_its_method_list_once(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=({"methods": ["Switch.Toggle"]}, 0.1)
        )

        await gateway.execute_component_action("192.168.1.100", "switch:0", "Toggle")
        await gateway.execute_component_action("192.168.1.100", "switch:0", "Toggle")

        assert self._methods_sent(mock_rpc_client) == [
            "Shelly.ListMethods",
            "Switch.Toggle",
            "Switch.Toggle",
        ]

    async def test_it_asks_each_device_for_its_own_method_list(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=({"methods": ["Switch.Toggle"]}, 0.1)
        )

        await gateway.execute_component_action("192.168.1.100", "switch:0", "Toggle")
        await gateway.execute_component_action("192.168.1.101", "switch:0", "Toggle")

        assert self._methods_sent(mock_rpc_client).count("Shelly.ListMethods") == 2

    async def test_it_saves_the_next_action_a_round_trip_after_a_status_read(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[*self.STATUS_READS, ({}, 0.1)]
        )

        await gateway.get_device_status("192.168.1.100")
        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "Toggle"
        )

        assert result.success is True
        assert self._methods_sent(mock_rpc_client).count("Shelly.ListMethods") == 1

    async def test_it_asks_the_device_again_on_every_status_read(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[*self.STATUS_READS, *self.STATUS_READS]
        )

        await gateway.get_device_status("192.168.1.100")
        await gateway.get_device_status("192.168.1.100")

        assert self._methods_sent(mock_rpc_client).count("Shelly.ListMethods") == 2

    async def test_it_does_not_let_a_caller_grow_a_remembered_list(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=({"methods": ["Switch.Toggle"]}, 0.1)
        )

        reported = await gateway._get_available_methods("192.168.1.100")
        reported.append("Switch.Nonsense")

        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "Switch.Nonsense"
        )

        assert result.success is False

    async def test_it_asks_the_device_again_before_refusing_a_remembered_miss(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": ["Switch.Toggle"]}, 0.1),
                ({}, 0.1),
                ({"methods": ["Switch.Set"]}, 0.1),
                ({}, 0.1),
            ]
        )

        await gateway.execute_component_action("192.168.1.100", "switch:0", "Toggle")
        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "Set"
        )

        assert result.success is True
        assert self._methods_sent(mock_rpc_client) == [
            "Shelly.ListMethods",
            "Switch.Toggle",
            "Shelly.ListMethods",
            "Switch.Set",
        ]

    async def test_it_sends_a_remembered_method_the_device_has_since_dropped(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                ({"methods": ["Switch.Toggle"]}, 0.1),
                ({}, 0.1),
                Exception("unknown method"),
            ]
        )

        await gateway.execute_component_action("192.168.1.100", "switch:0", "Toggle")
        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "Toggle"
        )

        assert result.success is False
        assert "unknown method" in result.message
        assert self._methods_sent(mock_rpc_client) == [
            "Shelly.ListMethods",
            "Switch.Toggle",
            "Switch.Toggle",
        ]

    async def test_it_asks_only_once_when_a_remembered_list_already_refuses(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=({"methods": ["Switch.Toggle"]}, 0.1)
        )

        result = await gateway.execute_component_action(
            "192.168.1.100", "switch:0", "Nonsense"
        )

        assert result.success is False
        assert self._methods_sent(mock_rpc_client) == ["Shelly.ListMethods"]

    async def test_it_does_not_remember_an_unanswered_method_list(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[
                Exception("ListMethods timed out"),
                ({}, 0.1),
                ({"methods": ["Switch.Toggle"]}, 0.1),
                ({}, 0.1),
            ]
        )

        await gateway.execute_component_action("192.168.1.100", "switch:0", "Toggle")
        await gateway.execute_component_action("192.168.1.100", "switch:0", "Toggle")

        assert self._methods_sent(mock_rpc_client) == [
            "Shelly.ListMethods",
            "Switch.Toggle",
            "Shelly.ListMethods",
            "Switch.Toggle",
        ]
