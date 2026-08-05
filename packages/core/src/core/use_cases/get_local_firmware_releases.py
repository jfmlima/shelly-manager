"""Use case for previewing the firmware a local update would install."""

from core.domain.entities.exceptions import DeviceNotFoundError
from core.domain.enums.enums import UpdateChannel
from core.domain.value_objects.base_device_request import BaseDeviceRequest
from core.domain.value_objects.firmware_release import FirmwareRelease
from core.gateways.device import DeviceGateway
from core.gateways.firmware import FirmwareGateway


class GetLocalFirmwareReleases:
    """Resolve what the firmware index publishes for one device, per channel.

    Backs the channel choice in the update dialog: an offline device cannot
    report what is available, so the manager answers from the same index a
    local update would install from.
    """

    def __init__(
        self,
        device_gateway: DeviceGateway,
        firmware_gateway: FirmwareGateway,
    ):
        self._device_gateway = device_gateway
        self._firmware_gateway = firmware_gateway

    async def execute(
        self, request: BaseDeviceRequest
    ) -> dict[str, FirmwareRelease | None]:
        """Releases by channel name, ``None`` where the index publishes nothing.

        A device local updates cannot serve (Gen1, or one reporting no app
        name) gets all-``None``: the dialog needs "nothing to offer", not an
        error, to disable the start button.

        Raises:
            DeviceNotFoundError: If the device is unreachable.
            FirmwareError: If the index cannot be queried.
        """
        ip = request.device_ip
        status = await self._device_gateway.get_device_status(ip)
        if status is None:
            raise DeviceNotFoundError(ip)

        if status.gen == 1 or not status.app_name:
            return {channel.value: None for channel in UpdateChannel}

        return {
            channel.value: await self._firmware_gateway.get_latest(
                status.app_name, channel.value
            )
            for channel in UpdateChannel
        }
