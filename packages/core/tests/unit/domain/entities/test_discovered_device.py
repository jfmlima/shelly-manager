from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status, UpdateChannel


def _device(device_type: str | None) -> DiscoveredDevice:
    return DiscoveredDevice(
        ip="192.168.1.100", status=Status.DETECTED, device_type=device_type
    )


class TestDiscoveredDeviceModelName:
    def test_it_derives_model_name_from_device_type(self):
        assert _device("SNSW-102P16EU").model_name == "Shelly Plus 2PM"

    def test_it_returns_none_for_unmapped_device_type(self):
        assert _device("NOT-A-MODEL").model_name is None
        assert _device(None).model_name is None

    def test_it_serializes_model_name(self):
        dumped = _device("SHSW-1").model_dump()
        assert dumped["model_name"] == "Shelly 1"


class TestDiscoveredDeviceIsBetaOnlyUpdate:
    def _update(self, **overrides) -> DiscoveredDevice:
        defaults = {
            "ip": "192.168.1.100",
            "status": Status.UPDATE_AVAILABLE,
            "available_firmware_version": "1.1.0-beta1",
            "available_firmware_channel": UpdateChannel.BETA,
        }
        return DiscoveredDevice(**{**defaults, **overrides})

    def test_it_flags_an_update_available_only_on_beta(self):
        assert self._update().is_beta_only_update() is True

    def test_it_does_not_flag_a_stable_update(self):
        device = self._update(
            available_firmware_version="1.1.0",
            available_firmware_channel=UpdateChannel.STABLE,
        )
        assert device.is_beta_only_update() is False

    def test_it_does_not_flag_a_device_without_an_update(self):
        device = self._update(
            status=Status.NO_UPDATE_NEEDED,
            available_firmware_version=None,
            available_firmware_channel=None,
        )
        assert device.is_beta_only_update() is False
