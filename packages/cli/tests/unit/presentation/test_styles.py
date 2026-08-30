import pytest
from cli.presentation.styles import (
    Colors,
    format_device_status,
    get_device_status_label,
    get_device_status_style,
)
from core.domain.enums.enums import Status


class TestGetDeviceStatusLabel:

    @pytest.mark.parametrize(
        "status,expected",
        [
            (Status.DETECTED, "Detected"),
            (Status.UPDATED, "Updated"),
            (Status.UPDATE_AVAILABLE, "Update Available"),
            (Status.NO_UPDATE_NEEDED, "Up to Date"),
            (Status.AUTH_REQUIRED, "Auth Required"),
            (Status.NOT_SHELLY, "Not a Shelly Device"),
            (Status.UNREACHABLE, "Unreachable"),
            (Status.ERROR, "Error"),
        ],
    )
    def test_it_labels_every_known_status(self, status, expected):
        assert get_device_status_label(status) == expected
        assert get_device_status_label(status.value) == expected

    def test_it_title_cases_an_unrecognized_status(self):
        assert get_device_status_label("something_new") == "Something New"

    def test_it_falls_back_to_unknown_for_an_empty_status(self):
        assert get_device_status_label("") == "Unknown"


class TestGetDeviceStatusStyle:

    def test_it_resolves_the_same_color_for_a_string_or_an_enum(self):
        assert (
            get_device_status_style(Status.UPDATE_AVAILABLE)
            == get_device_status_style("update_available")
            == Colors.DEVICE_UPDATE_AVAILABLE
        )

    def test_it_falls_back_to_unknown_for_an_unmapped_status(self):
        assert get_device_status_style("something_new") == Colors.DEVICE_UNKNOWN


class TestFormatDeviceStatus:

    def test_it_wraps_the_label_in_the_matching_color_style(self):
        style = get_device_status_style("update_available")

        result = format_device_status("update_available")

        assert result == f"[{style}]Update Available[/{style}]"

    def test_it_never_leaks_the_raw_enum_token(self):
        result = format_device_status("no_update_needed")

        assert "no_update_needed" not in result
        assert "Up to Date" in result
