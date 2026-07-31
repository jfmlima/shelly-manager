"""Tests for the update device from local use case."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.exceptions import (
    DeviceNotFoundError,
    FirmwareConfigurationError,
    FirmwareError,
)
from core.domain.entities.firmware_bundle import FirmwareBundle
from core.domain.value_objects.action_result import ActionResult
from core.domain.value_objects.base_device_request import BaseDeviceRequest
from core.domain.value_objects.firmware_release import FirmwareRelease
from core.settings import FirmwareSettings
from core.use_cases.update_device_from_local import UpdateDeviceFromLocal

IP = "192.168.1.100"
BASE_URL = "http://192.168.40.252:8000"


def _status(gen=2, app_name="Plus2PM", firmware_version="20240101-000000/1.7.5-gabc"):
    return SimpleNamespace(
        gen=gen,
        app_name=app_name,
        firmware_version=firmware_version,
    )


def _release(version="1.8.0"):
    return FirmwareRelease(
        app_name="Plus2PM",
        version=version,
        build_id=f"20250611-100000/{version}-g1234567",
        download_url="https://fwcdn.example.test/Plus2PM.zip",
        channel="stable",
    )


def _bundle(bundle_id=7, version="1.8.0"):
    return FirmwareBundle(
        id=bundle_id,
        app_name="Plus2PM",
        version=version,
        build_id=f"20250611-100000/{version}-g1234567",
        file_name=f"Plus2PM-{version}.zip",
    )


def _use_case(
    mock_device_gateway,
    mock_firmware_gateway,
    mock_acquire,
    advertised_base_url=BASE_URL,
):
    return UpdateDeviceFromLocal(
        device_gateway=mock_device_gateway,
        firmware_gateway=mock_firmware_gateway,
        acquire_firmware=mock_acquire,
        settings=FirmwareSettings(advertised_base_url=advertised_base_url),
    )


class TestUpdateDeviceFromLocal:
    @pytest.fixture
    def mock_firmware_gateway(self):
        gateway = AsyncMock()
        gateway.get_latest = AsyncMock(return_value=_release())
        return gateway

    @pytest.fixture
    def mock_acquire(self):
        acquire = AsyncMock()
        acquire.execute = AsyncMock(return_value=_bundle())
        return acquire

    @pytest.fixture
    def use_case(self, mock_device_gateway, mock_firmware_gateway, mock_acquire):
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                device_ip=IP,
                action_type="shelly.Update",
                success=True,
                message="Update executed successfully on shelly",
            )
        )
        return _use_case(mock_device_gateway, mock_firmware_gateway, mock_acquire)

    async def test_it_sends_the_local_url_to_the_device(
        self, use_case, mock_device_gateway, mock_firmware_gateway, mock_acquire
    ):
        result = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert result.success is True
        mock_device_gateway.execute_component_action.assert_awaited_once_with(
            IP,
            "shelly",
            "Update",
            {"url": f"{BASE_URL}/api/firmware/7/download"},
        )
        mock_firmware_gateway.get_latest.assert_awaited_once()
        mock_acquire.execute.assert_awaited_once_with(
            "Plus2PM", mock_firmware_gateway.get_latest.return_value
        )

    async def test_it_normalizes_a_trailing_slash_in_the_base_url(
        self, mock_device_gateway, mock_firmware_gateway, mock_acquire
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=_status())
        mock_device_gateway.execute_component_action = AsyncMock(
            return_value=ActionResult(
                device_ip=IP, action_type="shelly.Update", success=True, message="ok"
            )
        )
        use_case = _use_case(
            mock_device_gateway,
            mock_firmware_gateway,
            mock_acquire,
            advertised_base_url=f"{BASE_URL}/",
        )

        await use_case.execute(BaseDeviceRequest(device_ip=IP))

        mock_device_gateway.execute_component_action.assert_awaited_once_with(
            IP,
            "shelly",
            "Update",
            {"url": f"{BASE_URL}/api/firmware/7/download"},
        )

    async def test_it_rejects_an_unset_advertised_base_url(
        self, mock_device_gateway, mock_firmware_gateway, mock_acquire
    ):
        mock_device_gateway.get_device_status = AsyncMock()
        use_case = _use_case(
            mock_device_gateway,
            mock_firmware_gateway,
            mock_acquire,
            advertised_base_url=None,
        )

        with pytest.raises(FirmwareConfigurationError, match="ADVERTISED_BASE_URL"):
            await use_case.execute(BaseDeviceRequest(device_ip=IP))

        mock_device_gateway.get_device_status.assert_not_awaited()

    async def test_it_raises_when_the_device_is_unreachable(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(return_value=None)

        with pytest.raises(DeviceNotFoundError):
            await use_case.execute(BaseDeviceRequest(device_ip=IP))

    async def test_it_rejects_a_gen1_device(self, use_case, mock_device_gateway):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(gen=1, firmware_version="v1.14.0-gcb84623")
        )

        with pytest.raises(FirmwareError, match="Gen1"):
            await use_case.execute(BaseDeviceRequest(device_ip=IP))

        mock_device_gateway.execute_component_action.assert_not_awaited()

    async def test_it_rejects_a_device_without_an_app_name(
        self, use_case, mock_device_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(app_name=None)
        )

        with pytest.raises(FirmwareError, match="app name"):
            await use_case.execute(BaseDeviceRequest(device_ip=IP))

    async def test_it_raises_when_no_release_is_published(
        self, use_case, mock_firmware_gateway, mock_device_gateway
    ):
        mock_firmware_gateway.get_latest = AsyncMock(return_value=None)

        with pytest.raises(FirmwareError, match="No firmware published"):
            await use_case.execute(BaseDeviceRequest(device_ip=IP))

        mock_device_gateway.execute_component_action.assert_not_awaited()

    async def test_it_short_circuits_when_already_up_to_date(
        self, use_case, mock_device_gateway, mock_firmware_gateway, mock_acquire
    ):
        published = _release("1.7.5")
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version=published.build_id)
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=published)

        result = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert result.success is True
        assert "already" in result.message
        mock_acquire.execute.assert_not_awaited()
        mock_device_gateway.execute_component_action.assert_not_awaited()

    async def test_it_trusts_a_bare_version_a_device_reports(
        self, use_case, mock_device_gateway, mock_firmware_gateway, mock_acquire
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="1.7.5")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.7.5"))

        result = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert "already" in result.message
        mock_acquire.execute.assert_not_awaited()
        mock_device_gateway.execute_component_action.assert_not_awaited()

    async def test_it_reports_a_downgrade_from_a_bare_version(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="2.0.0")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.8.0"))

        result = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert "downgrade from 2.0.0 to 1.8.0" in result.message

    async def test_it_updates_a_version_republished_under_a_new_build(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="20240101-000000/1.7.5-gold")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.7.5"))

        await use_case.execute(BaseDeviceRequest(device_ip=IP))

        mock_device_gateway.execute_component_action.assert_awaited_once()

    async def test_it_installs_an_older_build_and_says_so(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="20260101-000000/1.9.0-gabc")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.8.0"))

        result = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert result.success is True
        assert "downgrade from 1.9.0 to 1.8.0" in result.message
        mock_device_gateway.execute_component_action.assert_awaited_once()

    async def test_it_reports_a_downgrade_from_a_prerelease(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="20260101-000000/1.9.0-beta1-gabc")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.8.0"))

        result = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert "downgrade from 1.9.0-beta1 to 1.8.0" in result.message
        mock_device_gateway.execute_component_action.assert_awaited_once()

    async def test_it_says_nothing_extra_when_moving_forward(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="20240101-000000/1.7.5-gabc")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.8.0"))

        result = await use_case.execute(BaseDeviceRequest(device_ip=IP))

        assert "downgrade" not in result.message

    async def test_it_updates_a_device_running_an_older_version(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="20240101-000000/1.7.5-gabc")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.8.0"))

        await use_case.execute(BaseDeviceRequest(device_ip=IP))

        mock_device_gateway.execute_component_action.assert_awaited_once()

    async def test_it_updates_when_the_versions_cannot_be_compared(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="20240101-000000/experimental-gabc")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.8.0"))

        await use_case.execute(BaseDeviceRequest(device_ip=IP))

        mock_device_gateway.execute_component_action.assert_awaited_once()

    async def test_it_updates_when_the_installed_version_is_a_prefix(
        self, use_case, mock_device_gateway, mock_firmware_gateway
    ):
        mock_device_gateway.get_device_status = AsyncMock(
            return_value=_status(firmware_version="20240101-000000/1.7.5-gabc")
        )
        mock_firmware_gateway.get_latest = AsyncMock(return_value=_release("1.7.55"))

        await use_case.execute(BaseDeviceRequest(device_ip=IP))

        mock_device_gateway.execute_component_action.assert_awaited_once()
