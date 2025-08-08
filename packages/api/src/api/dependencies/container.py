"""
Dependency injection container for API layer.
"""

import os
from pathlib import Path
from typing import Any

from core.gateways.configuration.file_configuration_gateway import (
    FileConfigurationGateway,
)
from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway
from core.gateways.network.async_shelly_rpc_client import AsyncShellyRPCClient
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.reboot_device import RebootDeviceUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase


class APIContainer:
    def __init__(self, config_file_path: str | None = None) -> None:
        if config_file_path is None:
            # Try to find config.json by looking upward from current directory
            config_file_path = self._find_config_file()
        self._config_file_path = config_file_path
        self._instances: dict[str, Any] = {}

    def _find_config_file(self) -> str | None:
        current_path = Path.cwd()
        while current_path != current_path.parent:
            config_path = current_path / "config.json"
            if config_path.exists():
                return str(config_path)
            current_path = current_path.parent

        # Also check for environment variable
        config_from_env = os.getenv("SHELLY_CONFIG_FILE")
        if config_from_env and Path(config_from_env).exists():
            return config_from_env

        return None

    def get_rpc_client(self) -> AsyncShellyRPCClient:
        if "rpc_client" not in self._instances:
            self._instances["rpc_client"] = AsyncShellyRPCClient()
        rpc_client: AsyncShellyRPCClient = self._instances["rpc_client"]
        return rpc_client

    def get_device_gateway(self) -> ShellyDeviceGateway:
        if "device_gateway" not in self._instances:
            rpc_client = self.get_rpc_client()
            self._instances["device_gateway"] = ShellyDeviceGateway(rpc_client)
        device_gateway: ShellyDeviceGateway = self._instances["device_gateway"]
        return device_gateway

    def get_config_gateway(self) -> FileConfigurationGateway:
        if "config_gateway" not in self._instances:
            self._instances["config_gateway"] = FileConfigurationGateway(
                self._config_file_path
            )
        config_gateway: FileConfigurationGateway = self._instances["config_gateway"]
        return config_gateway

    def get_scan_interactor(self) -> ScanDevicesUseCase:
        if "scan_interactor" not in self._instances:
            self._instances["scan_interactor"] = ScanDevicesUseCase(
                device_gateway=self.get_device_gateway(),
                config_gateway=self.get_config_gateway(),
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

    def get_device_config_set_interactor(self) -> SetConfigurationUseCase:
        if "device_config_set_interactor" not in self._instances:
            self._instances["device_config_set_interactor"] = SetConfigurationUseCase(
                device_gateway=self.get_device_gateway()
            )
        device_config_set_interactor: SetConfigurationUseCase = self._instances[
            "device_config_set_interactor"
        ]
        return device_config_set_interactor
