"""Shared container providing gateway, repository and interactor factories."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from core.gateways.device import LegacyDeviceGateway
from core.gateways.device.ap_device_detector import APDeviceDetector
from core.gateways.device.legacy_component_mapper import LegacyComponentMapper
from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway
from core.gateways.network import (
    AsyncShellyRPCClient,
    LegacyHttpClient,
    MDNSGateway,
    ZeroconfMDNSClient,
)
from core.repositories.db import async_session_factory
from core.repositories.sqlalchemy_backup_repository import (
    SQLAlchemyBackupRepository,
)
from core.repositories.sqlalchemy_backup_schedule_repository import (
    SQLAlchemyBackupScheduleRepository,
)
from core.repositories.sqlalchemy_credentials_repository import (
    SQLAlchemyCredentialsRepository,
)
from core.repositories.sqlalchemy_provisioning_profile_repository import (
    SQLAlchemyProvisioningProfileRepository,
)
from core.services.auth_state_cache import AuthStateCache
from core.services.authentication_service import AuthenticationService
from core.services.encryption_service import EncryptionService
from core.settings import settings as core_settings
from core.use_cases.backup_device_config import BackupDeviceConfig
from core.use_cases.bulk_operations import BulkOperationsUseCase
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.execute_component_action import ExecuteComponentActionUseCase
from core.use_cases.get_component_actions import GetComponentActionsUseCase
from core.use_cases.manage_backup_schedules import ManageBackupSchedulesUseCase
from core.use_cases.manage_provisioning_profiles import (
    ManageProvisioningProfilesUseCase,
)
from core.use_cases.provision_device import ProvisionDeviceUseCase
from core.use_cases.restore_device_config import RestoreDeviceConfig
from core.use_cases.run_due_backups import RunDueBackupsUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase


class BaseContainer:
    def __init__(self) -> None:
        self._device_gateway: ShellyDeviceGateway | None = None
        self._legacy_http_client: LegacyHttpClient | None = None
        self._mdns_client: MDNSGateway | None = None
        self._scan_interactor: ScanDevicesUseCase | None = None
        self._execute_component_action_interactor: (
            ExecuteComponentActionUseCase | None
        ) = None
        self._component_actions_interactor: GetComponentActionsUseCase | None = None
        self._status_interactor: CheckDeviceStatusUseCase | None = None
        self._bulk_operations_interactor: BulkOperationsUseCase | None = None
        self._manage_profiles_interactor: ManageProvisioningProfilesUseCase | None = (
            None
        )
        self._provision_device_interactor: ProvisionDeviceUseCase | None = None
        self._ap_device_detector: APDeviceDetector | None = None
        self._backup_device_config_interactor: BackupDeviceConfig | None = None
        self._restore_device_config_interactor: RestoreDeviceConfig | None = None
        self._manage_backup_schedules_interactor: (
            ManageBackupSchedulesUseCase | None
        ) = None
        self._run_due_backups_interactor: RunDueBackupsUseCase | None = None
        # Every slot above is a device-scoped cache cleared by
        # _reset_device_caches(); slots below survive close().
        self._device_cache_slots: tuple[str, ...] = tuple(vars(self))
        self._rpc_client: AsyncShellyRPCClient | None = None
        self._auth_service: AuthenticationService | None = None
        self._encryption_service: EncryptionService | None = None
        self._auth_state_cache: AuthStateCache | None = None

    def get_rpc_client(self) -> AsyncShellyRPCClient:
        if self._rpc_client is None:
            self._rpc_client = AsyncShellyRPCClient(
                timeout=core_settings.network.timeout,
                connect_timeout=core_settings.network.connect_timeout,
                verify=core_settings.network.verify_ssl,
                authentication_service=self.get_authentication_service(),
                auth_state_cache=self.get_auth_state_cache(),
            )
        return self._rpc_client

    def get_device_gateway(self) -> ShellyDeviceGateway:
        if self._device_gateway is None:
            legacy_http_client = LegacyHttpClient(
                connect_timeout=core_settings.network.connect_timeout,
            )
            self._legacy_http_client = legacy_http_client
            legacy_component_mapper = LegacyComponentMapper()
            legacy_gateway = LegacyDeviceGateway(
                http_client=legacy_http_client,
                component_mapper=legacy_component_mapper,
                authentication_service=self.get_authentication_service(),
                auth_state_cache=self.get_auth_state_cache(),
            )

            self._device_gateway = ShellyDeviceGateway(
                rpc_client=self.get_rpc_client(),
                legacy_gateway=legacy_gateway,
                auth_state_cache=self.get_auth_state_cache(),
            )
        return self._device_gateway

    async def _aclose_legacy_http_client(self) -> None:
        if self._legacy_http_client is not None:
            try:
                await self._legacy_http_client.close()
            except Exception:
                pass

    def _reset_device_caches(self) -> None:
        for slot in self._device_cache_slots:
            setattr(self, slot, None)

    def get_encryption_service(self) -> EncryptionService:
        if self._encryption_service is None:
            self._encryption_service = EncryptionService()
        return self._encryption_service

    def get_authentication_service(self) -> AuthenticationService:
        if self._auth_service is None:
            self._auth_service = AuthenticationService(
                repository_factory=self.create_credentials_repository
            )
        return self._auth_service

    def get_mdns_client(self) -> MDNSGateway:
        if self._mdns_client is None:
            self._mdns_client = ZeroconfMDNSClient()
        return self._mdns_client

    def get_auth_state_cache(self) -> AuthStateCache:
        if self._auth_state_cache is None:
            self._auth_state_cache = AuthStateCache()
        return self._auth_state_cache

    def get_scan_interactor(self) -> ScanDevicesUseCase:
        if self._scan_interactor is None:
            self._scan_interactor = ScanDevicesUseCase(
                device_gateway=self.get_device_gateway(),
                mdns_client=self.get_mdns_client(),
                auth_state_cache=self.get_auth_state_cache(),
            )
        return self._scan_interactor

    def get_execute_component_action_interactor(self) -> ExecuteComponentActionUseCase:
        if self._execute_component_action_interactor is None:
            self._execute_component_action_interactor = ExecuteComponentActionUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._execute_component_action_interactor

    def get_component_actions_interactor(self) -> GetComponentActionsUseCase:
        if self._component_actions_interactor is None:
            self._component_actions_interactor = GetComponentActionsUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._component_actions_interactor

    def get_status_interactor(self) -> CheckDeviceStatusUseCase:
        if self._status_interactor is None:
            self._status_interactor = CheckDeviceStatusUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._status_interactor

    def get_bulk_operations_interactor(self) -> BulkOperationsUseCase:
        if self._bulk_operations_interactor is None:
            self._bulk_operations_interactor = BulkOperationsUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._bulk_operations_interactor

    def get_ap_device_detector(self) -> APDeviceDetector:
        if self._ap_device_detector is None:
            self._ap_device_detector = APDeviceDetector()
        return self._ap_device_detector

    def get_manage_profiles_interactor(self) -> ManageProvisioningProfilesUseCase:
        if self._manage_profiles_interactor is None:
            self._manage_profiles_interactor = ManageProvisioningProfilesUseCase(
                repository_factory=self.create_provisioning_profile_repository,
            )
        return self._manage_profiles_interactor

    def get_provision_device_interactor(self) -> ProvisionDeviceUseCase:
        if self._provision_device_interactor is None:
            self._provision_device_interactor = ProvisionDeviceUseCase(
                rpc_client=self.get_rpc_client(),
                detector=self.get_ap_device_detector(),
                profile_repository_factory=self.create_provisioning_profile_repository,
                credentials_repository_factory=self.create_credentials_repository,
            )
        return self._provision_device_interactor

    def get_backup_device_config_interactor(self) -> BackupDeviceConfig:
        if self._backup_device_config_interactor is None:
            self._backup_device_config_interactor = BackupDeviceConfig(
                device_gateway=self.get_device_gateway(),
                bulk_operations=self.get_bulk_operations_interactor(),
                repository_factory=self.create_backup_repository,
            )
        return self._backup_device_config_interactor

    def get_restore_device_config_interactor(self) -> RestoreDeviceConfig:
        if self._restore_device_config_interactor is None:
            self._restore_device_config_interactor = RestoreDeviceConfig(
                device_gateway=self.get_device_gateway(),
                repository_factory=self.create_backup_repository,
            )
        return self._restore_device_config_interactor

    def get_manage_backup_schedules_interactor(self) -> ManageBackupSchedulesUseCase:
        if self._manage_backup_schedules_interactor is None:
            self._manage_backup_schedules_interactor = ManageBackupSchedulesUseCase(
                repository_factory=self.create_backup_schedule_repository,
            )
        return self._manage_backup_schedules_interactor

    def get_run_due_backups_interactor(self) -> RunDueBackupsUseCase:
        if self._run_due_backups_interactor is None:
            self._run_due_backups_interactor = RunDueBackupsUseCase(
                schedule_repository_factory=self.create_backup_schedule_repository,
                backup_repository_factory=self.create_backup_repository,
                credentials_repository_factory=self.create_credentials_repository,
                backup_device_config=self.get_backup_device_config_interactor(),
                scan_devices=self.get_scan_interactor(),
            )
        return self._run_due_backups_interactor

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

    @asynccontextmanager
    async def create_provisioning_profile_repository(
        self,
    ) -> AsyncGenerator[SQLAlchemyProvisioningProfileRepository, None]:
        async with async_session_factory() as session:
            try:
                yield SQLAlchemyProvisioningProfileRepository(
                    session, self.get_encryption_service()
                )
            finally:
                await session.close()

    @asynccontextmanager
    async def create_backup_repository(
        self,
    ) -> AsyncGenerator[SQLAlchemyBackupRepository, None]:
        async with async_session_factory() as session:
            try:
                yield SQLAlchemyBackupRepository(session, self.get_encryption_service())
            finally:
                await session.close()

    @asynccontextmanager
    async def create_backup_schedule_repository(
        self,
    ) -> AsyncGenerator[SQLAlchemyBackupScheduleRepository, None]:
        async with async_session_factory() as session:
            try:
                yield SQLAlchemyBackupScheduleRepository(session)
            finally:
                await session.close()

    async def close(self) -> None:
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

        await self._aclose_legacy_http_client()

        self._rpc_client = None
        self._reset_device_caches()
