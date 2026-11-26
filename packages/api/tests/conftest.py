"""Test configuration and shared fixtures for API tests."""

import os

# Generate a valid Fernet key for tests before any other imports.
# This must happen before settings.py is imported.
# NOTE: noqa comments prevent linters from reordering these imports.
if "SHELLY_SECRET_KEY" not in os.environ:  # noqa: E402
    from cryptography.fernet import Fernet

    os.environ["SHELLY_SECRET_KEY"] = Fernet.generate_key().decode()


import pytest  # noqa: E402
from api.main import create_app  # noqa: E402


@pytest.fixture
def app():
    return create_app()
