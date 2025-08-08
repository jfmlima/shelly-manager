"""
Dependency injection container for CLI.
"""

from pathlib import Path
from typing import Any

import requests
from core.gateways.configuration.file_configuration_gateway import (
    FileConfigurationGateway,
)
from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway
from core.gateways.network.shelly_rpc_client import ShellyRPCClient
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.reboot_device import RebootDeviceUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase


class CLIContainer:
    def __init__(self, config_file_path: str | None = None) -> None:
        if config_file_path is None:
            current_path = Path(__file__).resolve()
            for parent in current_path.parents:
                config_path = parent / "config.json"
                if config_path.exists():
                    config_file_path = str(config_path)
                    break
        self._config_file_path = config_file_path
        self._instances: dict[str, Any] = {}

    def get_rpc_client(self) -> ShellyRPCClient:
        if "rpc_client" not in self._instances:
            session = requests.Session()
            self._instances["rpc_client"] = ShellyRPCClient(session)
        rpc_client: ShellyRPCClient = self._instances["rpc_client"]
        return rpc_client

    def get_device_gateway(self) -> ShellyDeviceGateway:
        if "device_gateway" not in self._instances:
            rpc_client = self.get_rpc_client()
            self._instances["device_gateway"] = ShellyDeviceGateway(rpc_client)
        device_gateway: ShellyDeviceGateway = self._instances["device_gateway"]
        return device_gateway

    def get_scan_interactor(self) -> ScanDevicesUseCase:
        if "scan_interactor" not in self._instances:

            self._instances["scan_interactor"] = ScanDevicesUseCase(
                device_gateway=self.get_device_gateway(),
                config_gateway=FileConfigurationGateway(self._config_file_path),
            )
        scan_interactor: ScanDevicesUseCase = self._instances["scan_interactor"]
        return scan_interactor

    def get_update_interactor(self) -> UpdateDeviceFirmwareUseCase:
        if "update_interactor" not in self._instances:
            self._instances["update_interactor"] = UpdateDeviceFirmwareUseCase(
                device_gateway=self.get_device_gateway()
            )
        update_interactor: UpdateDeviceFirmwareUseCase = self._instances[
            "update_interactor"
        ]
        return update_interactor

    def get_reboot_interactor(self) -> RebootDeviceUseCase:
        if "reboot_interactor" not in self._instances:
            self._instances["reboot_interactor"] = RebootDeviceUseCase(
                device_gateway=self.get_device_gateway()
            )
        reboot_interactor: RebootDeviceUseCase = self._instances["reboot_interactor"]
        return reboot_interactor

    def get_status_interactor(self) -> CheckDeviceStatusUseCase:
        if "status_interactor" not in self._instances:
            self._instances["status_interactor"] = CheckDeviceStatusUseCase(
                device_gateway=self.get_device_gateway()
            )
        status_interactor: CheckDeviceStatusUseCase = self._instances[
            "status_interactor"
        ]
        return status_interactor

    def get_device_config_interactor(self) -> GetConfigurationUseCase:
        if "device_config_interactor" not in self._instances:
            self._instances["device_config_interactor"] = GetConfigurationUseCase(
                device_gateway=self.get_device_gateway()
            )
        device_config_interactor: GetConfigurationUseCase = self._instances[
            "device_config_interactor"
        ]
        return device_config_interactor

    def get_set_device_config_interactor(self) -> SetConfigurationUseCase:
        """Returns interactor to update configuration directly on the device (kept)."""
        if "set_device_config_interactor" not in self._instances:
            self._instances["set_device_config_interactor"] = SetConfigurationUseCase(
                device_gateway=self.get_device_gateway()
            )
        set_device_config_interactor: SetConfigurationUseCase = self._instances[
            "set_device_config_interactor"
        ]
        return set_device_config_interactor

    def get_export_interactor(self) -> GetConfigurationUseCase:
        """Returns interactor for exporting device configurations."""
        return self.get_device_config_interactor()

    def get_device_scan_interactor(self) -> ScanDevicesUseCase:
        """Returns interactor for scanning devices."""
        return self.get_scan_interactor()
