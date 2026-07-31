import json

import pytest
from core.domain.entities.exceptions import ValidationError
from core.settings import AppSettings


def test_it_loads_backup_settings_from_config_file(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "backup": {
                    "scheduler_enabled": False,
                    "poll_interval_seconds": 300,
                }
            }
        )
    )

    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )

    settings = AppSettings(config_file=str(config_path))

    assert settings.backup.scheduler_enabled is False
    assert settings.backup.poll_interval_seconds == 300


def test_it_saves_backup_settings_to_config_file(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"

    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )

    settings = AppSettings(config_file=str(config_path))
    settings.backup.scheduler_enabled = False
    settings.backup.poll_interval_seconds = 300
    settings.save_config()

    saved = json.loads(config_path.read_text())
    assert saved["backup"] == {
        "scheduler_enabled": False,
        "poll_interval_seconds": 300,
    }


def test_it_loads_firmware_settings_from_config_file(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "firmware": {
                    "dir": str(tmp_path / "fw"),
                    "advertised_base_url": "http://192.168.40.252:8000",
                }
            }
        )
    )

    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )

    settings = AppSettings(config_file=str(config_path))

    assert settings.firmware.dir == str(tmp_path / "fw")
    assert settings.firmware.advertised_base_url == "http://192.168.40.252:8000"
    assert settings.firmware.index_url == "https://updates.shelly.cloud/update"


def test_it_saves_firmware_settings_to_config_file(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"

    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )

    settings = AppSettings(config_file=str(config_path))
    settings.firmware.advertised_base_url = "http://192.168.40.252:8000"
    settings.save_config()

    saved = json.loads(config_path.read_text())
    assert saved["firmware"] == {
        "dir": "./data/firmware",
        "advertised_base_url": "http://192.168.40.252:8000",
        "index_url": "https://updates.shelly.cloud/update",
        "verify_ssl": False,
        "allowed_download_hosts": "shelly.cloud",
    }


def test_it_reads_a_comma_separated_download_allow_list(monkeypatch):
    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )
    monkeypatch.setenv(
        "SHELLY_FIRMWARE_ALLOWED_DOWNLOAD_HOSTS", "shelly.cloud, Mirror.Example.com "
    )

    settings = AppSettings(config_file="does-not-exist.json")

    assert settings.firmware.download_host_allow_list() == [
        "shelly.cloud",
        "mirror.example.com",
    ]


def test_it_keeps_the_default_when_the_download_allow_list_is_blank(monkeypatch):
    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )
    monkeypatch.setenv("SHELLY_FIRMWARE_ALLOWED_DOWNLOAD_HOSTS", "  , ")

    settings = AppSettings(config_file="does-not-exist.json")

    assert settings.firmware.download_host_allow_list() == ["shelly.cloud"]


def test_it_accepts_any_download_host_only_when_asked_explicitly(monkeypatch):
    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )
    monkeypatch.setenv("SHELLY_FIRMWARE_ALLOWED_DOWNLOAD_HOSTS", "*")

    settings = AppSettings(config_file="does-not-exist.json")

    assert settings.firmware.download_host_allow_list() == []


def test_it_creates_the_firmware_dir_on_validate(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )

    settings = AppSettings(config_file=str(tmp_path / "config.json"))
    settings.data_dir = str(tmp_path / "data")
    settings.firmware.dir = str(tmp_path / "data" / "firmware")
    settings.validate_settings()

    assert (tmp_path / "data" / "firmware").is_dir()


def test_it_builds_without_a_secret_key(monkeypatch):
    monkeypatch.delenv("SHELLY_SECRET_KEY", raising=False)

    settings = AppSettings(config_file="does-not-exist.json", _env_file=None)

    assert settings.secret_key is None


def test_it_rejects_a_missing_secret_key_on_validate(tmp_path, monkeypatch):
    monkeypatch.delenv("SHELLY_SECRET_KEY", raising=False)

    settings = AppSettings(config_file=str(tmp_path / "config.json"), _env_file=None)
    settings.data_dir = str(tmp_path / "data")
    settings.firmware.dir = str(tmp_path / "data" / "firmware")

    with pytest.raises(ValidationError) as excinfo:
        settings.validate_settings()

    assert "SHELLY_SECRET_KEY" in str(excinfo.value)
