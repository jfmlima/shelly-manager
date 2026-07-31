"""Tests for the shared BaseContainer wiring."""

from unittest.mock import AsyncMock

import pytest
from core.dependencies.container_base import BaseContainer
from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway
from core.gateways.network import AsyncShellyRPCClient
from core.repositories.sqlalchemy_backup_repository import (
    SQLAlchemyBackupRepository,
)
from core.repositories.sqlalchemy_backup_schedule_repository import (
    SQLAlchemyBackupScheduleRepository,
)
from core.repositories.sqlalchemy_credentials_repository import (
    SQLAlchemyCredentialsRepository,
)
from core.repositories.sqlalchemy_firmware_repository import (
    SQLAlchemyFirmwareRepository,
)
from core.repositories.sqlalchemy_provisioning_profile_repository import (
    SQLAlchemyProvisioningProfileRepository,
)
from core.services.authentication_service import AuthenticationService

PERSISTENT_SLOTS = {
    "_rpc_client",
    "_auth_service",
    "_encryption_service",
    "_auth_state_cache",
}


@pytest.fixture
def container():
    c = BaseContainer()
    c._rpc_client = AsyncMock(spec=AsyncShellyRPCClient)
    c._mdns_client = AsyncMock()
    return c


class TestProviderWiring:
    def test_it_builds_and_caches_the_device_gateway(self, container):
        gateway = container.get_device_gateway()

        assert isinstance(gateway, ShellyDeviceGateway)
        assert container.get_device_gateway() is gateway

    async def test_it_builds_the_rpc_client_with_auth_wiring(self):
        container = BaseContainer()

        client = container.get_rpc_client()
        try:
            assert isinstance(client, AsyncShellyRPCClient)
            assert (
                client.authentication_service is container.get_authentication_service()
            )
            assert client.auth_state_cache is container.get_auth_state_cache()
            assert container.get_rpc_client() is client
        finally:
            await client.close()

    async def test_it_gives_the_device_gateway_the_shared_auth_state_cache(self):
        container = BaseContainer()

        try:
            gateway = container.get_device_gateway()

            assert gateway._auth_state_cache is container.get_auth_state_cache()
        finally:
            await container.close()

    def test_it_wires_the_auth_service_to_the_credentials_factory(self, container):
        service = container.get_authentication_service()

        assert isinstance(service, AuthenticationService)
        assert service.repository_factory == container.create_credentials_repository

    @pytest.mark.parametrize(
        "getter",
        [
            "get_scan_interactor",
            "get_execute_component_action_interactor",
            "get_component_actions_interactor",
            "get_status_interactor",
            "get_bulk_operations_interactor",
            "get_manage_profiles_interactor",
            "get_provision_device_interactor",
            "get_backup_device_config_interactor",
            "get_restore_device_config_interactor",
            "get_manage_backup_schedules_interactor",
            "get_run_due_backups_interactor",
            "get_firmware_gateway",
            "get_acquire_firmware_interactor",
            "get_update_device_from_local_interactor",
            "get_manage_firmware_interactor",
            "get_ap_device_detector",
            "get_mdns_client",
            "get_auth_state_cache",
            "get_encryption_service",
            "get_authentication_service",
        ],
    )
    def test_it_caches_each_provider(self, container, getter):
        first = getattr(container, getter)()

        assert first is not None
        assert getattr(container, getter)() is first


class TestRepositoryFactories:
    @pytest.mark.parametrize(
        "factory,expected_type",
        [
            ("create_credentials_repository", SQLAlchemyCredentialsRepository),
            (
                "create_provisioning_profile_repository",
                SQLAlchemyProvisioningProfileRepository,
            ),
            ("create_backup_repository", SQLAlchemyBackupRepository),
            (
                "create_backup_schedule_repository",
                SQLAlchemyBackupScheduleRepository,
            ),
            ("create_firmware_repository", SQLAlchemyFirmwareRepository),
        ],
    )
    async def test_it_yields_a_repository_per_session(
        self, container, factory, expected_type
    ):
        async with getattr(container, factory)() as repo:
            assert isinstance(repo, expected_type)


class TestClose:
    async def test_it_closes_clients_and_rebuilds_device_resources(self):
        container = BaseContainer()
        rpc = AsyncMock(spec=AsyncShellyRPCClient)
        mdns = AsyncMock()
        container._rpc_client = rpc
        container._mdns_client = mdns
        gateway = container.get_device_gateway()
        auth_service = container.get_authentication_service()

        await container.close()

        rpc.close.assert_awaited_once()
        mdns.close.assert_awaited_once()
        assert container._rpc_client is None
        assert container.get_device_gateway() is not gateway
        assert container.get_authentication_service() is auth_service
        await container.close()

    async def test_it_closes_the_firmware_gateway(self):
        container = BaseContainer()
        firmware_gateway = AsyncMock()
        container._firmware_gateway = firmware_gateway

        await container.close()

        firmware_gateway.close.assert_awaited_once()
        assert container._firmware_gateway is None

    async def test_it_swallows_client_close_errors(self):
        container = BaseContainer()
        rpc = AsyncMock(spec=AsyncShellyRPCClient)
        rpc.close.side_effect = RuntimeError("already closed")
        container._rpc_client = rpc

        await container.close()

        assert container._rpc_client is None

    def test_it_resets_every_slot_except_declared_persistent_ones(self):
        container = BaseContainer()
        sentinel = object()
        slots = [name for name in vars(container) if name != "_device_cache_slots"]
        for name in slots:
            setattr(container, name, sentinel)

        container._reset_device_caches()

        survivors = {name for name in slots if getattr(container, name) is sentinel}
        assert survivors == PERSISTENT_SLOTS
