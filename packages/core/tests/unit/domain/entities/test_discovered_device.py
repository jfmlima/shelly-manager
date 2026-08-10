from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status


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
