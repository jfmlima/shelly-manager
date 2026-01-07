"""Dependency injection container for CLI using shared BaseContainer."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from core.dependencies.container_base import BaseContainer
from core.gateways.network.async_shelly_rpc_client import AsyncShellyRPCClient
from core.repositories.db import async_session_factory
from core.repositories.sqlalchemy_credentials_repository import (
    SQLAlchemyCredentialsRepository,
)
from core.services.authentication_service import AuthenticationService
from core.services.encryption_service import EncryptionService
from core.use_cases.scan_devices import ScanDevicesUseCase


class CLIContainer(BaseContainer):
    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: AsyncShellyRPCClient | None = None
        self._auth_service: AuthenticationService | None = None
        self._encryption_service: EncryptionService | None = None

    def get_encryption_service(self) -> EncryptionService:
        if self._encryption_service is None:
            self._encryption_service = EncryptionService()
        return self._encryption_service

    @asynccontextmanager
    async def create_credentials_repository(
        self,
    ) -> AsyncGenerator[SQLAlchemyCredentialsRepository, None]:
        async with async_session_factory() as session:
            try:
                yield SQLAlchemyCredentialsRepository(
                    session, self.get_encryption_service()
                )
            finally:
                await session.close()

    def get_authentication_service(self) -> AuthenticationService:
        if self._auth_service is None:
            self._auth_service = AuthenticationService(
                repository_factory=self.create_credentials_repository
            )
        return self._auth_service

    def get_rpc_client(self) -> AsyncShellyRPCClient:
        if self._rpc_client is None:
            # Shared session for connection pooling
            http_session = httpx.AsyncClient(timeout=3.0)
            self._rpc_client = AsyncShellyRPCClient(
                session=http_session,
                authentication_service=self.get_authentication_service(),
            )
        return self._rpc_client

    # Backwards compatibility helpers (optional convenience wrappers)
    def get_device_scan_interactor(self) -> ScanDevicesUseCase:
        return self.get_scan_interactor()
