"""Dependency injection container for CLI using shared BaseContainer."""

import requests
from core.dependencies.container_base import BaseContainer
from core.gateways.network.shelly_rpc_client import ShellyRPCClient
from core.use_cases.scan_devices import ScanDevicesUseCase


class CLIContainer(BaseContainer):
    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: ShellyRPCClient | None = None

    def get_rpc_client(self) -> ShellyRPCClient:
        if self._rpc_client is None:
            session = requests.Session()
            self._rpc_client = ShellyRPCClient(session)
        return self._rpc_client

    # Backwards compatibility helpers (optional convenience wrappers)
    def get_device_scan_interactor(self) -> ScanDevicesUseCase:
        return self.get_scan_interactor()
