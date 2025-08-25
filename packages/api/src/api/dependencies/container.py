"""
Dependency injection container for API layer.
"""

from pathlib import Path

from core.dependencies.container_base import BaseContainer
from core.gateways.configuration.file_configuration_gateway import (
    FileConfigurationGateway,
)
from core.gateways.network.async_shelly_rpc_client import AsyncShellyRPCClient
from core.settings import settings as core_settings
from core.utils.path import resolve_config_path
from litestar.di import Provide


class APIContainer(BaseContainer):
    def __init__(self, config_file_path: str | None = None) -> None:
        super().__init__()
        self._rpc_client: AsyncShellyRPCClient | None = None
        self._config_gateway: FileConfigurationGateway | None = None
        self._config_file_path: str | None = resolve_config_path(
            config_file_path, start=Path.cwd()
        )

    def get_rpc_client(self) -> AsyncShellyRPCClient:
        if self._rpc_client is None:
            self._rpc_client = AsyncShellyRPCClient(
                timeout=int(core_settings.network.timeout),
                verify=core_settings.network.verify_ssl,
            )
        return self._rpc_client

    def get_config_gateway(self) -> FileConfigurationGateway:
        if self._config_gateway is None:
            self._config_gateway = FileConfigurationGateway(self._config_file_path)
        return self._config_gateway

    async def close(self) -> None:
        """Gracefully close async resources."""
        if self._rpc_client is not None:
            try:
                await self._rpc_client.close()
            except Exception:
                pass

        if self._mdns_client is not None:
            try:
                await self._mdns_client.close()
            except Exception:
                pass


def get_dependencies(container: APIContainer) -> dict:
    return {
        "scan_interactor": Provide(
            lambda: container.get_scan_interactor(), sync_to_thread=False
        ),
        "execute_component_action_interactor": Provide(
            lambda: container.get_execute_component_action_interactor(),
            sync_to_thread=False,
        ),
        "component_actions_interactor": Provide(
            lambda: container.get_component_actions_interactor(),
            sync_to_thread=False,
        ),
        "status_interactor": Provide(
            lambda: container.get_status_interactor(), sync_to_thread=False
        ),
        "bulk_operations_use_case": Provide(
            lambda: container.get_bulk_operations_interactor(),
            sync_to_thread=False,
        ),
    }
