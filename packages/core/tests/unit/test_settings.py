import json

from core.settings import AppSettings, NetworkSettings


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


def test_it_builds_without_a_secret_key(monkeypatch):
    monkeypatch.delenv("SHELLY_SECRET_KEY", raising=False)

    settings = AppSettings(config_file="does-not-exist.json", _env_file=None)

    assert settings.secret_key is None


def test_it_builds_with_auth_disabled_by_default(monkeypatch):
    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )
    monkeypatch.delenv("SHELLY_AUTH_TOKEN", raising=False)

    settings = AppSettings(config_file="does-not-exist.json", _env_file=None)

    assert settings.auth_token is None


def test_it_reads_the_auth_token_from_the_environment(monkeypatch):
    monkeypatch.setenv(
        "SHELLY_SECRET_KEY", "0N6fK7YkEmvA0I4d1sD4v15uvB94H4A1N1nMG8vLMOg="
    )
    monkeypatch.setenv("SHELLY_AUTH_TOKEN", "my-auth-token")

    settings = AppSettings(config_file="does-not-exist.json", _env_file=None)

    assert settings.auth_token == "my-auth-token"


def test_it_retries_a_scanned_address_once_by_default(monkeypatch):
    monkeypatch.delenv("NETWORK_RETRY_ATTEMPTS", raising=False)
    monkeypatch.delenv("NETWORK_RETRY_DELAY", raising=False)

    network = NetworkSettings()

    assert network.retry_attempts == 1
    assert network.retry_delay == 0.5


def test_it_ignores_keys_in_the_env_file_that_are_not_settings(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("PORT=9000\nCOMPOSE_PROJECT_NAME=shelly\n")
    monkeypatch.chdir(tmp_path)

    settings = AppSettings(config_file="does-not-exist.json")

    assert settings.data_dir == "./data"


def test_it_reads_every_section_from_the_env_file(tmp_path, monkeypatch):
    values = {
        "NETWORK_TIMEOUT": "5",
        "LOG_LEVEL": "DEBUG",
        "SHELLY_BACKUP_SCHEDULER_ENABLED": "false",
        "SHELLY_FIRMWARE_ADVERTISED_BASE_URL": "http://192.168.40.252:8000",
        "SHELLY_DATA_DIR": "/srv/shelly",
    }
    for key in values:
        monkeypatch.delenv(key, raising=False)
    lines = "".join(f"{key}={value}\n" for key, value in values.items())
    (tmp_path / ".env").write_text(lines)
    monkeypatch.chdir(tmp_path)

    settings = AppSettings(config_file="does-not-exist.json")

    assert settings.network.timeout == 5.0
    assert settings.logging.level == "DEBUG"
    assert settings.backup.scheduler_enabled is False
    assert settings.firmware.advertised_base_url == "http://192.168.40.252:8000"
    assert settings.data_dir == "/srv/shelly"
