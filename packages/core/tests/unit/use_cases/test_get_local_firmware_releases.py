"""Tests for the local firmware release preview use case."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, call

import pytest
from core.domain.entities.exceptions import DeviceNotFoundError, FirmwareError
from core.domain.value_objects.base_device_request import BaseDeviceRequest
from core.domain.value_objects.firmware_release import FirmwareRelease
from core.use_cases.get_local_firmware_releases import GetLocalFirmwareReleases

IP = "192.168.1.100"


def _status(gen=2, app_name="Plus2PM"):
    return SimpleNamespace(gen=gen, app_name=app_name)


def _release(channel, version="1.8.0"):
    return FirmwareRelease(
        app_name="Plus2PM",
        version=version,
        build_id=f"20250611-100000/{version}-g1234567",
        download_url="https://fwcdn.example.test/Plus2PM.zip",
        channel=channel,
    )


class TestGetLocalFirmwareReleases:
    @pytest.fixture
    def mock_firmware_gateway(self):
        gateway = AsyncMock()
        gateway.get_latest = AsyncMock(
            side_effect=lambda app_name, channel: _release(channel)
        )
        return gateway

    @pytest.fixture
    def use_case(self, mock_device_gateway, mock_firmware_gateway):
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        return GetLocalFirmwareReleases(
            device_gateway=mock_device_gateway,
            firmware_gateway=mock_firmware_gateway,
        )

    async def test_it_returns_a_release_per_channel(
        self, use_case, mock_firmware_gateway
    ):
        releases = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert set(releases) == {"stable", "beta"}
        assert releases["stable"].channel == "stable"
        assert releases["beta"].channel == "beta"
        mock_firmware_gateway.get_latest.assert_has_awaits(
            [call("Plus2PM", "stable"), call("Plus2PM", "beta")]
        )

    async def test_it_passes_through_a_channel_without_a_release(
        self, use_case, mock_firmware_gateway
    ):
        mock_firmware_gateway.get_latest.side_effect = lambda app_name, channel: (
            _release(channel) if channel == "stable" else None
        )

        releases = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert releases["stable"] is not None
        assert releases["beta"] is None

    async def test_it_raises_when_the_device_is_unreachable(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        with pytest.raises(DeviceNotFoundError):
            await use_case.execute(BaseDeviceRequest(device_ip=IP))

    async def test_it_offers_nothing_for_a_gen1_device(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status(gen=1))

        releases = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert releases == {"stable": None, "beta": None}
        mock_firmware_gateway.get_latest.assert_not_awaited()

    async def test_it_offers_nothing_without_an_app_name(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(app_name=None)
        )

        releases = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert releases == {"stable": None, "beta": None}
        mock_firmware_gateway.get_latest.assert_not_awaited()

    async def test_it_propagates_an_index_failure(
        self, use_case, mock_firmware_gateway
    ):
        mock_firmware_gateway.get_latest.side_effect = FirmwareError("index down")

        with pytest.raises(FirmwareError):
            await use_case.execute(BaseDeviceRequest(device_ip=IP))
