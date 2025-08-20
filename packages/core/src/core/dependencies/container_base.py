"""Shared container base providing common gateway and interactor factories (no cast)."""

from typing import Any

from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway
from core.use_cases.bulk_operations import BulkOperationsUseCase
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.execute_component_action import ExecuteComponentActionUseCase
from core.use_cases.get_component_actions import GetComponentActionsUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase


class BaseContainer:
    def __init__(self) -> None:
        self._device_gateway: ShellyDeviceGateway | None = None
        self._scan_interactor: ScanDevicesUseCase | None = None
        self._execute_component_action_interactor: (
            ExecuteComponentActionUseCase | None
        ) = None
        self._component_actions_interactor: GetComponentActionsUseCase | None = None
        self._status_interactor: CheckDeviceStatusUseCase | None = None
        self._device_config_interactor: GetConfigurationUseCase | None = None
        self._device_config_set_interactor: SetConfigurationUseCase | None = None
        self._bulk_operations_interactor: BulkOperationsUseCase | None = None

    def get_rpc_client(self) -> Any:
        raise NotImplementedError

    def get_config_gateway(self) -> Any:
        raise NotImplementedError

    def get_device_gateway(self) -> ShellyDeviceGateway:
        if self._device_gateway is None:
            self._device_gateway = ShellyDeviceGateway(self.get_rpc_client())
        return self._device_gateway

    def get_scan_interactor(self) -> ScanDevicesUseCase:
        if self._scan_interactor is None:
            self._scan_interactor = ScanDevicesUseCase(
                device_gateway=self.get_device_gateway(),
                config_gateway=self.get_config_gateway(),
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

    def get_device_config_interactor(self) -> GetConfigurationUseCase:
        if self._device_config_interactor is None:
            self._device_config_interactor = GetConfigurationUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._device_config_interactor

    def get_device_config_set_interactor(self) -> SetConfigurationUseCase:
        if self._device_config_set_interactor is None:
            self._device_config_set_interactor = SetConfigurationUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._device_config_set_interactor

    def get_bulk_operations_interactor(self) -> BulkOperationsUseCase:
        if self._bulk_operations_interactor is None:
            self._bulk_operations_interactor = BulkOperationsUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._bulk_operations_interactor
