"""Shared container base providing common gateway and interactor factories (no cast)."""

from typing import Any

from core.gateways.device.shelly_device_gateway import ShellyDeviceGateway
from core.use_cases.check_device_status import CheckDeviceStatusUseCase
from core.use_cases.get_configuration import GetConfigurationUseCase
from core.use_cases.reboot_device import RebootDeviceUseCase
from core.use_cases.scan_devices import ScanDevicesUseCase
from core.use_cases.set_configuration import SetConfigurationUseCase
from core.use_cases.update_device_firmware import UpdateDeviceFirmwareUseCase


class BaseContainer:
    def __init__(self) -> None:
        self._device_gateway: ShellyDeviceGateway | None = None
        self._scan_interactor: ScanDevicesUseCase | None = None
        self._update_interactor: UpdateDeviceFirmwareUseCase | None = None
        self._reboot_interactor: RebootDeviceUseCase | None = None
        self._status_interactor: CheckDeviceStatusUseCase | None = None
        self._device_config_interactor: GetConfigurationUseCase | None = None
        self._device_config_set_interactor: SetConfigurationUseCase | None = None

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

    def get_update_interactor(self) -> UpdateDeviceFirmwareUseCase:
        if self._update_interactor is None:
            self._update_interactor = UpdateDeviceFirmwareUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._update_interactor

    def get_reboot_interactor(self) -> RebootDeviceUseCase:
        if self._reboot_interactor is None:
            self._reboot_interactor = RebootDeviceUseCase(
                device_gateway=self.get_device_gateway()
            )
        return self._reboot_interactor

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
