import json

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
