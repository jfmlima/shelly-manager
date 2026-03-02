"""Shared container base providing common gateway and interactor factories (no cast)."""

from typing import Any

from core.gateways.device import LegacyDeviceGateway
from core.gateways.device.ap_device_detector import APDeviceDetector
from core.gateways.device.legacy_component_mapper import LegacyComponentMapper
from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway
from core.gateways.network import LegacyHttpClient, MDNSGateway, ZeroconfMDNSClient
from core.use_cases.bulk_operations import BulkOperationsUseCase
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.execute_component_action import ExecuteComponentActionUseCase
from core.use_cases.get_component_actions import GetComponentActionsUseCase
from core.use_cases.manage_provisioning_profiles import (
    ManageProvisioningProfilesUseCase,
)
from core.use_cases.provision_device import ProvisionDeviceUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase


class BaseContainer:
    def __init__(self) -> None:
        self._device_gateway: ShellyDeviceGateway | None = None
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

    def get_rpc_client(self) -> Any:
        raise NotImplementedError

    def get_device_gateway(self) -> ShellyDeviceGateway:
        if self._device_gateway is None:
            legacy_http_client = LegacyHttpClient()
            legacy_component_mapper = LegacyComponentMapper()
            legacy_gateway = LegacyDeviceGateway(
                http_client=legacy_http_client,
                component_mapper=legacy_component_mapper,
                authentication_service=self._get_authentication_service_optional(),
                auth_state_cache=self.get_auth_state_cache(),
            )

            self._device_gateway = ShellyDeviceGateway(
                rpc_client=self.get_rpc_client(),
                legacy_gateway=legacy_gateway,
            )
        return self._device_gateway

    def _get_authentication_service_optional(self) -> Any:
        """Return AuthenticationService if available, None otherwise."""
        if hasattr(self, "get_authentication_service"):
            return self.get_authentication_service()
        return None

    def get_mdns_client(self) -> MDNSGateway:
        if self._mdns_client is None:
            self._mdns_client = ZeroconfMDNSClient()
        return self._mdns_client

    def get_auth_state_cache(self) -> Any:
        from core.services.auth_state_cache import AuthStateCache

        if not hasattr(self, "_auth_state_cache"):
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

    def create_provisioning_profile_repository(self) -> Any:
        raise NotImplementedError

    def create_credentials_repository(self) -> Any:
        raise NotImplementedError
