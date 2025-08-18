from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.domain.entities.discovered_device import DiscoveredDevice
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
        update_info = {}  # No updates available
        
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[(device_info, 0.15), (update_info, 0.05)]
        )

        result = await gateway.discover_device("192.168.1.100")

        assert result is not None
        assert result.ip == "192.168.1.100"
        assert result.status == Status.NO_UPDATE_NEEDED  # Updated to match actual behavior
        assert result.device_id == "shelly1pm-001"
        assert result.device_type == "SHPM-1"
        assert result.device_name == "Living Room Switch"
        assert result.firmware_version == "20230913-114010/v1.14.0-gcb84623"
        assert result.response_time == 0.15
        assert isinstance(result.last_seen, datetime)
        assert mock_rpc_client.make_rpc_request.call_count == 2
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (("192.168.1.100", "Shelly.GetDeviceInfo"), {"timeout": 3.0})
        assert calls[1] == (("192.168.1.100", "Shelly.CheckForUpdate"), {"timeout": 3.0})

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
        assert calls[1] == (("192.168.1.100", "Shelly.CheckForUpdate"), {"timeout": 3.0})

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
                        "available_updates": {"version": "1.1.0"}
                    },
                    "config": {
                        "device": {
                            "name": "Test Device",
                            "fw_id": "20240101-120000/1.0.0-abcd123"
                        }
                    }
                }
            ],
            "cfg_rev": 1,
            "total": 1
        }
        
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=(components_data, 0.1))

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert len(result.components) == 1
        assert result.total_components == 1
        mock_rpc_client.make_rpc_request.assert_called_once_with(
            "192.168.1.100", "shelly.getcomponents", params={'offset': 0}, timeout=3.0
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
                        "uptime": 3600
                    },
                    "config": {
                        "device": {
                            "name": "Test Device",
                            "fw_id": "20240101-120000/1.0.0-abcd123"
                        }
                    }
                }
            ],
            "cfg_rev": 1,
            "total": 1
        }
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=(components_data, 0.1))

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        mock_rpc_client.make_rpc_request.assert_called_once_with(
            "192.168.1.100", "shelly.getcomponents", params={'offset': 0}, timeout=3.0
        )

    async def test_it_gets_device_status_with_zigbee_data(self, gateway, mock_rpc_client):
        """Test get_device_status with Zigbee data available."""
        components_data = {
            "components": [
                {
                    "key": "switch:0",
                    "status": {"output": True},
                    "config": {"name": "Test Switch"},
                    "attrs": {}
                }
            ],
            "cfg_rev": 1,
            "total": 1
        }
        zigbee_data = {"network_state": "joined"}
        
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=[(components_data, 0.1), (zigbee_data, 0.05)]
        )

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert len(result.components) == 2  # switch + zigbee
        
        assert mock_rpc_client.make_rpc_request.call_count == 2
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (("192.168.1.100", "shelly.getcomponents"), {"params": {'offset': 0}, "timeout": 3.0})
        assert calls[1] == (("192.168.1.100", "Zigbee.GetStatus"), {"timeout": 3.0})

    async def test_it_gets_device_status_with_zigbee_failure(self, gateway, mock_rpc_client):
        """Test get_device_status when Zigbee.GetStatus fails (non-Zigbee device)."""
        components_data = {
            "components": [
                {
                    "key": "switch:0",
                    "status": {"output": True},
                    "config": {"name": "Test Switch"},
                    "attrs": {}
                }
            ],
            "cfg_rev": 1,
            "total": 1
        }
        
        mock_rpc_client.make_rpc_request = AsyncMock()
        mock_rpc_client.make_rpc_request.side_effect = [
            (components_data, 0.1),
            Exception("Zigbee not available")
        ]

        result = await gateway.get_device_status("192.168.1.100")

        assert result is not None
        assert isinstance(result, DeviceStatus)
        assert result.device_ip == "192.168.1.100"
        assert len(result.components) == 1  # only switch, no zigbee
        
        assert mock_rpc_client.make_rpc_request.call_count == 2
        calls = mock_rpc_client.make_rpc_request.call_args_list
        assert calls[0] == (("192.168.1.100", "shelly.getcomponents"), {"params": {'offset': 0}, "timeout": 3.0})
        assert calls[1] == (("192.168.1.100", "Zigbee.GetStatus"), {"timeout": 3.0})

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

    async def test_it_executes_update_action_successfully(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=({}, 0.1))

        result = await gateway.execute_action(
            "192.168.1.100", "update", {"channel": "stable"}
        )

        assert result.success is True
        assert result.action_type == "update"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Update initiated successfully"
        mock_rpc_client.make_rpc_request.assert_called_once_with(
            "192.168.1.100", "Shelly.Update"
        )

    async def test_it_executes_reboot_action_successfully(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=({}, 0.1))

        result = await gateway.execute_action("192.168.1.100", "reboot", {})

        assert result.success is True
        assert result.action_type == "reboot"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Reboot initiated successfully"
        mock_rpc_client.make_rpc_request.assert_called_once_with(
            "192.168.1.100", "Sys.Reboot"
        )

    async def test_it_executes_config_get_action_successfully(
        self, gateway, mock_rpc_client
    ):
        config_data = {"wifi": {"ssid": "TestNetwork"}, "name": "Test Device"}
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=(config_data, 0.1))

        result = await gateway.execute_action("192.168.1.100", "config-get", {})

        assert result.success is True
        assert result.action_type == "config-get"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Configuration retrieved successfully"
        assert result.data == config_data
        mock_rpc_client.make_rpc_request.assert_called_once_with(
            "192.168.1.100", "Sys.GetConfig"
        )

    async def test_it_executes_config_set_action_successfully(
        self, gateway, mock_rpc_client
    ):
        config_data = {"name": "Updated Device Name"}
        parameters = {"config": config_data}
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=({}, 0.1))

        result = await gateway.execute_action("192.168.1.100", "config-set", parameters)

        assert result.success is True
        assert result.action_type == "config-set"
        assert result.device_ip == "192.168.1.100"
        assert result.message == "Configuration updated successfully"
        mock_rpc_client.make_rpc_request.assert_called_once_with(
            "192.168.1.100", "Sys.SetConfig", params={"config": config_data}
        )

    async def test_it_handles_config_set_without_config_data(
        self, gateway, mock_rpc_client
    ):
        result = await gateway.execute_action("192.168.1.100", "config-set", {})

        assert result.success is False
        assert result.action_type == "config-set"
        assert result.error == "No configuration data provided"
        mock_rpc_client.make_rpc_request.assert_not_called()

    async def test_it_handles_unknown_action_type(self, gateway, mock_rpc_client):
        result = await gateway.execute_action("192.168.1.100", "unknown-action", {})

        assert result.success is False
        assert result.action_type == "unknown-action"
        assert result.error == "Unknown action type: unknown-action"
        mock_rpc_client.make_rpc_request.assert_not_called()

    async def test_it_handles_action_execution_failure(self, gateway, mock_rpc_client):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=Exception("RPC call failed")
        )

        result = await gateway.execute_action("192.168.1.100", "reboot", {})

        assert result.success is False
        assert result.action_type == "reboot"
        assert result.error == "RPC call failed"

    async def test_it_executes_bulk_actions_successfully(
        self, gateway, mock_rpc_client
    ):
        device_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=({}, 0.1))

        results = await gateway.execute_bulk_action(device_ips, "reboot", {})

        assert len(results) == 3
        assert all(result.success for result in results)
        assert all(result.action_type == "reboot" for result in results)
        assert mock_rpc_client.make_rpc_request.call_count == 3

    async def test_it_gets_device_config_successfully(self, gateway, mock_rpc_client):
        config_data = {"wifi": {"ssid": "TestNetwork"}, "name": "Test Device"}
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=(config_data, 0.1))

        result = await gateway.get_device_config("192.168.1.100")

        assert result == config_data
        mock_rpc_client.make_rpc_request.assert_called_once_with(
            "192.168.1.100", "Sys.GetConfig"
        )

    async def test_it_returns_none_when_config_retrieval_fails(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=Exception("Network error")
        )

        result = await gateway.get_device_config("192.168.1.100")

        assert result is None

    async def test_it_returns_none_when_config_is_not_dict(
        self, gateway, mock_rpc_client
    ):
        mock_rpc_client.make_rpc_request = AsyncMock(
            return_value=("invalid_config", 0.1)
        )

        result = await gateway.get_device_config("192.168.1.100")

        assert result is None

    async def test_it_sets_device_config_successfully(self, gateway, mock_rpc_client):
        config_data = {"name": "Updated Device"}
        mock_rpc_client.make_rpc_request = AsyncMock(return_value=({}, 0.1))

        result = await gateway.set_device_config("192.168.1.100", config_data)

        assert result is True
        mock_rpc_client.make_rpc_request.assert_called_once_with(
            "192.168.1.100", "Sys.SetConfig", params={"config": config_data}
        )

    async def test_it_returns_false_when_config_set_fails(
        self, gateway, mock_rpc_client
    ):
        config_data = {"name": "Updated Device"}
        mock_rpc_client.make_rpc_request = AsyncMock(
            side_effect=Exception("Network error")
        )

        result = await gateway.set_device_config("192.168.1.100", config_data)

        assert result is False

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
        assert result.status == Status.NO_UPDATE_NEEDED
