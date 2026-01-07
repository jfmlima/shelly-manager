"""
Dependency injection container for API layer.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from core.dependencies.container_base import BaseContainer
from core.gateways.network.async_shelly_rpc_client import AsyncShellyRPCClient
from core.repositories.db import async_session_factory
from core.repositories.sqlalchemy_credentials_repository import (
    SQLAlchemyCredentialsRepository,
)
from core.services.authentication_service import AuthenticationService
from core.services.encryption_service import EncryptionService
from core.settings import settings as core_settings
from core.use_cases.manage_credentials import ManageCredentialsUseCase
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession


class APIContainer(BaseContainer):
    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: AsyncShellyRPCClient | None = None
        self._auth_service: AuthenticationService | None = None
        self._encryption_service: EncryptionService | None = None
        self._credentials_use_case: ManageCredentialsUseCase | None = None

    def get_encryption_service(self) -> EncryptionService:
        if self._encryption_service is None:
            self._encryption_service = EncryptionService()
        return self._encryption_service

    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    def get_credentials_repository(
        self, session: AsyncSession
    ) -> SQLAlchemyCredentialsRepository:
        return SQLAlchemyCredentialsRepository(session, self.get_encryption_service())

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
            self._rpc_client = AsyncShellyRPCClient(
                timeout=int(core_settings.network.timeout),
                verify=core_settings.network.verify_ssl,
                authentication_service=self.get_authentication_service(),
                auth_state_cache=self.get_auth_state_cache(),
            )
        return self._rpc_client

    def get_credentials_use_case(self) -> ManageCredentialsUseCase:
        if self._credentials_use_case is None:

            def on_credential_changed(mac: str) -> None:
                self.get_rpc_client().invalidate_credential_cache(mac)

            self._credentials_use_case = ManageCredentialsUseCase(
                repository_factory=self.create_credentials_repository,
                on_credential_changed=on_credential_changed,
            )
        return self._credentials_use_case

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
        "db_session": Provide(
            container.get_db_session,
            sync_to_thread=False,
        ),
        "credentials_use_case": Provide(
            lambda: container.get_credentials_use_case(),
            sync_to_thread=False,
        ),
        "authentication_service": Provide(
            lambda: container.get_authentication_service(),
            sync_to_thread=False,
        ),
    }
