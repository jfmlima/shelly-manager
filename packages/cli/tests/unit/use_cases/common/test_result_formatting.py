from unittest.mock import MagicMock

import pytest
from cli.use_cases.common.result_formatting import ResultFormatter
from core.domain.entities.components.system import SystemComponent
from core.domain.entities.device_status import DeviceStatus
from core.domain.entities.discovered_device import DiscoveredDevice
from core.domain.enums.enums import Status
from rich.panel import Panel


class TestEffectiveStatus:

    @pytest.fixture
    def formatter(self):
        return ResultFormatter(MagicMock())

    def _device(self, **overrides):
        defaults = {
            "ip": "192.168.1.100",
            "status": Status.UPDATE_AVAILABLE,
            "device_id": "test-device",
            "device_type": "SHSW-1",
            "firmware_version": "1.0.0",
            "available_firmware_version": "1.1.0-beta1",
            "available_firmware_channel": "beta",
        }
        return DiscoveredDevice(**{**defaults, **overrides})

    def test_it_hides_a_beta_only_update_by_default(self, formatter):
        device = self._device()

        assert (
            formatter._effective_status(device, include_beta=False)
            == Status.NO_UPDATE_NEEDED.value
        )

    def test_it_surfaces_a_beta_only_update_when_included(self, formatter):
        device = self._device()

        assert (
            formatter._effective_status(device, include_beta=True)
            == Status.UPDATE_AVAILABLE.value
        )

    def test_it_leaves_a_stable_update_alone_either_way(self, formatter):
        device = self._device(
            available_firmware_version="1.1.0", available_firmware_channel="stable"
        )

        assert (
            formatter._effective_status(device, include_beta=False)
            == Status.UPDATE_AVAILABLE.value
        )
        assert (
            formatter._effective_status(device, include_beta=True)
            == Status.UPDATE_AVAILABLE.value
        )

    def test_it_leaves_a_device_without_updates_alone(self, formatter):
        device = self._device(
            status=Status.NO_UPDATE_NEEDED,
            available_firmware_version=None,
            available_firmware_channel=None,
        )

        assert (
            formatter._effective_status(device, include_beta=False)
            == Status.NO_UPDATE_NEEDED.value
        )


class TestFormatDetailedDeviceStatusBetaFiltering:

    @pytest.fixture
    def mock_console(self):
        return MagicMock()

    @pytest.fixture
    def formatter(self, mock_console):
        return ResultFormatter(mock_console)

    def _device_status(self):
        sys_component = SystemComponent(
            key="sys",
            component_type="sys",
            device_name="Test Device",
            firmware_version="1.0.0",
            available_updates={
                "stable": {"version": "1.1.0"},
                "beta": {"version": "1.2.0-beta1", "name": "beta"},
            },
        )
        return DeviceStatus(device_ip="192.168.1.100", components=[sys_component])

    def _printed_text(self, mock_console) -> str:
        chunks = []
        for call in mock_console.print.call_args_list:
            if not call.args:
                continue
            obj = call.args[0]
            chunks.append(str(obj.renderable) if isinstance(obj, Panel) else str(obj))
        return "\n".join(chunks)

    def test_it_hides_the_beta_release_by_default(self, formatter, mock_console):
        formatter.format_detailed_device_status(self._device_status())

        output = self._printed_text(mock_console)
        assert "1.1.0" in output
        assert "1.2.0-beta1" not in output

    def test_it_shows_the_beta_release_when_included(self, formatter, mock_console):
        formatter.format_detailed_device_status(
            self._device_status(), include_beta=True
        )

        output = self._printed_text(mock_console)
        assert "1.1.0" in output
        assert "1.2.0-beta1" in output

    def _beta_only_device_status(self):
        sys_component = SystemComponent(
            key="sys",
            component_type="sys",
            device_name="Test Device",
            firmware_version="1.0.0",
            available_updates={"beta": {"version": "1.2.0-beta1", "name": "beta"}},
        )
        return DeviceStatus(device_ip="192.168.1.100", components=[sys_component])

    def test_it_shows_nothing_when_only_a_hidden_beta_exists(
        self, formatter, mock_console
    ):
        formatter.format_detailed_device_status(self._beta_only_device_status())

        output = self._printed_text(mock_console)
        assert "1.2.0-beta1" not in output
        assert "Updates Available" not in output

    def test_it_shows_the_beta_only_release_when_included(
        self, formatter, mock_console
    ):
        formatter.format_detailed_device_status(
            self._beta_only_device_status(), include_beta=True
        )

        output = self._printed_text(mock_console)
        assert "1.2.0-beta1" in output
