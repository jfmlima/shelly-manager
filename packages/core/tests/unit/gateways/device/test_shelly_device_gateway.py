from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.domain.entities.device_status import DeviceStatus
from core.domain.enums.enums import Status
from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway


class TestShellyDeviceGateway:

    @pytest.fixture
    def mock_rpc_client(self):
        return MagicMock()

    @pytest.fixture
    def gateway(self, mock_rpc_client):
        return ShellyDeviceGateway(rpc_client=mock_rpc_client)

    async def test_it_discovers_device_successfully(self, gateway, mock_rpc_client):
        device_info = {
            "id": "shelly1pm-001",
            "model": "SHPM-1",
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
        assert result.device_name == "Living Room Switch"
        assert result.firmware_version == "20230913-114010/v1.14.0-gcb84623"
        assert result.response_time == 0.15
        assert isinstance(result.last_seen, datetime)
        assert mock_rpc_client.make_rpc_request.call_count == 2
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (("192.168.1.100", "Shelly.GetDeviceInfo"), {"timeout": 3.0})
        assert calls[1] == (
            ("192.168.1.100", "Shelly.CheckForUpdate"),
            {"timeout": 3.0},
        )

    async def test_it_discovers_device_with_custom_timeout(
        self, gateway, mock_rpc_client
    ):
        device_info = {"id": "test-device", "model": "SHSW-1", "fw_id": "1.0.0"}
        update_info = {}

        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[(device_info, 0.2), (update_info, 0.05)]
        )

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert mock_rpc_client.make_rpc_request.call_count == 2
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (("192.168.1.100", "Shelly.GetDeviceInfo"), {"timeout": 3.0})
        assert calls[1] == (
            ("192.168.1.100", "Shelly.CheckForUpdate"),
            {"timeout": 3.0},
        )

    async def test_it_handles_device_discovery_failure(self, gateway, mock_rpc_client):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=Exception("Network timeout")
        )

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
                Exception("Zigbee not available"),
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
            "192.168.1.100", "Shelly.GetComponents", params={"offset": 0}, timeout=3.0
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
                Exception("Zigbee not available"),
                (["Sys.Reboot", "Sys.GetConfig"], 0.05),
            ]
        )

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert mock_rpc_client.make_rpc_request.call_count == 4
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.GetComponents", params={"offset": 0}, timeout=3.0
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
                (zigbee_data, 0.05),
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
        assert calls[0] == (("192.168.1.100", "Shelly.GetDeviceInfo"), {"timeout": 3.0})
        assert calls[1] == (
            ("192.168.1.100", "Shelly.GetComponents"),
            {"params": {"offset": 0}, "timeout": 3.0},
        )
        assert calls[2] == (("192.168.1.100", "Zigbee.GetStatus"), {"timeout": 3.0})
        assert calls[3] == (("192.168.1.100", "Shelly.ListMethods"), {"timeout": 3.0})

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
            Exception("Zigbee not available"),
            (["Switch.Set"], 0.05),
        ]

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert len(result.components) == 1

        assert mock_rpc_client.make_rpc_request.call_count == 4
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (("192.168.1.100", "Shelly.GetDeviceInfo"), {"timeout": 3.0})
        assert calls[1] == (
            ("192.168.1.100", "Shelly.GetComponents"),
            {"params": {"offset": 0}, "timeout": 3.0},
        )
        assert calls[2] == (("192.168.1.100", "Zigbee.GetStatus"), {"timeout": 3.0})
        assert calls[3] == (("192.168.1.100", "Shelly.ListMethods"), {"timeout": 3.0})

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
            "192.168.1.100", "Shelly.ListMethods", timeout=3.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.Update", params=None, timeout=3.0
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
            "192.168.1.100", "Shelly.ListMethods", timeout=3.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Shelly.Reboot", params=None, timeout=3.0
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
            "192.168.1.100", "Shelly.ListMethods", timeout=3.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Sys.GetConfig", params=None, timeout=3.0
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
            "192.168.1.100", "Shelly.ListMethods", timeout=3.0
        )
        mock_rpc_client.make_rpc_request.assert_any_call(
            "192.168.1.100", "Sys.SetConfig", params=None, timeout=3.0
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
        assert "not found in available methods" in result.error
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
        assert "not found in available methods" in result.error
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
            Exception("Zigbee not available"),
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
            {"timeout": 3.0},
        )

        assert calls[1] == (
            ("192.168.1.100", "Shelly.GetComponents"),
            {"params": {"offset": 0}, "timeout": 3.0},
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

        assert result is None

        assert mock_rpc_client.make_rpc_request.call_count == 2
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (
            ("192.168.1.100", "Shelly.GetDeviceInfo"),
            {"timeout": 3.0},
        )
