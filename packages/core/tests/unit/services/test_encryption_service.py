import importlib

import pytest
from core.domain.entities.exceptions import ConfigurationError
from core.services.encryption_service import EncryptionService

VALID_KEY = "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="


def test_it_round_trips_with_an_injected_key():
    service = EncryptionService(VALID_KEY)

    assert service.decrypt(service.encrypt("hunter2")) == "hunter2"


def test_it_falls_back_to_the_configured_key(monkeypatch):
    monkeypatch.setenv("SHELLY_SECRET_KEY", VALID_KEY)
    settings_module = importlib.import_module("core.settings")
    monkeypatch.setattr(settings_module.settings, "secret_key", VALID_KEY)

    service = EncryptionService()

    assert service.decrypt(service.encrypt("hunter2")) == "hunter2"


def test_it_names_the_env_var_when_no_key_is_configured(monkeypatch):
    settings_module = importlib.import_module("core.settings")
    monkeypatch.setattr(settings_module.settings, "secret_key", None)

    with pytest.raises(ConfigurationError) as excinfo:
        EncryptionService()

    assert "SHELLY_SECRET_KEY" in str(excinfo.value)
