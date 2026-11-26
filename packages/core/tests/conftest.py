"""Test fixtures for core package tests."""

import os

# settings.py reads SHELLY_SECRET_KEY at import, so the key is set before any
# core import.
if "SHELLY_SECRET_KEY" not in os.environ:  # noqa: E402
    from cryptography.fernet import Fernet

    os.environ["SHELLY_SECRET_KEY"] = Fernet.generate_key().decode()

from unittest.mock import MagicMock  # noqa: E402

import pytest  # noqa: E402
from core.gateways.device import DeviceGateway  # noqa: E402


@pytest.fixture
def mock_device_gateway():
    gateway = MagicMock(spec=DeviceGateway)
    return gateway
