"""Tests for core enumerations."""

import pytest
from core.domain.enums.enums import UpdateChannel


class TestUpdateChannel:
    def test_it_sends_no_parameters_for_the_stable_channel(self):
        assert UpdateChannel.STABLE.to_update_parameters() == {}

    def test_it_names_the_channel_for_beta(self):
        assert UpdateChannel.BETA.to_update_parameters() == {"channel": "beta"}

    def test_it_rejects_an_unknown_channel(self):
        with pytest.raises(ValueError):
            UpdateChannel("nightly")
