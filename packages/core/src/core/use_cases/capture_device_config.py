"""Use case for capturing one device's configuration into a snapshot."""

from core.domain.entities.config_snapshot import DeviceSnapshot, SnapshotDeviceInfo
from core.domain.entities.device_status import DeviceStatus
from core.domain.value_objects.generation import Generation
from core.gateways.device import DeviceGateway
from core.use_cases.capture_strategies import ComponentCaptureStrategy
from core.use_cases.capture_strategies.gen1 import Gen1CaptureStrategy
from core.use_cases.capture_strategies.gen2 import Gen2CaptureStrategy


class CaptureDeviceConfig:
    """Produce a :class:`DeviceSnapshot` for a device whose status is known.

    The single producer of the snapshot shape: the bulk export and a stored
    backup are the same capture, differing only in what the caller does with
    it. Callers own the status fetch, so neither pays for a second one.
    """

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway
        self._gen1_capture = Gen1CaptureStrategy(device_gateway)
        self._gen2_capture = Gen2CaptureStrategy(device_gateway)

    async def capture(
        self,
        device_ip: str,
        status: DeviceStatus,
        component_types: list[str],
    ) -> DeviceSnapshot:
        """Capture the requested component types off one device."""
        strategy = self._capture_strategy(status)
        return DeviceSnapshot(
            device_info=SnapshotDeviceInfo.from_status(status),
            components=await strategy.capture_components(
                device_ip, status, component_types
            ),
        )

    def _capture_strategy(self, status: DeviceStatus) -> ComponentCaptureStrategy:
        if Generation.from_device_gen(status.gen) is Generation.GEN1:
            return self._gen1_capture
        return self._gen2_capture
