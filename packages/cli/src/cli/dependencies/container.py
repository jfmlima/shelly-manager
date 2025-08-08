"""Dependency injection container for CLI using shared BaseContainer."""

from pathlib import Path

import requests
from core.dependencies.container_base import BaseContainer
from core.gateways.configuration.file_configuration_gateway import (
    FileConfigurationGateway,
)
from core.gateways.network.shelly_rpc_client import ShellyRPCClient
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.utils.path import resolve_config_path


class CLIContainer(BaseContainer):
    def __init__(self, config_file_path: str | None = None) -> None:
        super().__init__()
        self._rpc_client: ShellyRPCClient | None = None
        self._config_gateway: FileConfigurationGateway | None = None
        self._config_file_path: str | None = resolve_config_path(
            config_file_path, start=Path(__file__).resolve()
        )

    def get_rpc_client(self) -> ShellyRPCClient:
        if self._rpc_client is None:
            session = requests.Session()
            self._rpc_client = ShellyRPCClient(session)
        return self._rpc_client

    def get_config_gateway(self) -> FileConfigurationGateway:
        if self._config_gateway is None:
            self._config_gateway = FileConfigurationGateway(self._config_file_path)
        return self._config_gateway

    # Backwards compatibility helpers (optional convenience wrappers)
    def get_export_interactor(self) -> GetConfigurationUseCase:
        return self.get_device_config_interactor()

    def get_device_scan_interactor(self) -> ScanDevicesUseCase:
        return self.get_scan_interactor()
