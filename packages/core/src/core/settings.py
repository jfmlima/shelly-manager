"""
Configuration management for the Shelly Manager application.
"""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.domain.entities.exceptions import ConfigurationError

MISSING_SECRET_KEY_MESSAGE = (
    "SHELLY_SECRET_KEY is not set. Generate one with: "
    "openssl rand -base64 32 | tr '+/' '-_'"
)

INVALID_SECRET_KEY_MESSAGE = (
    "SHELLY_SECRET_KEY is not a valid Fernet key. Generate one with: "
    "openssl rand -base64 32 | tr '+/' '-_'."
)

# Every section reads the same env file with its own prefix. The file also holds
# the other sections' keys and docker compose's, so keys a section does not
# have are ignored.
ENV_FILE_CONFIG = SettingsConfigDict(
    env_file=".env", env_file_encoding="utf-8", extra="ignore"
)


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOG_", **ENV_FILE_CONFIG)

    level: str = Field(default="INFO", description="Logging level")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid logging level. Must be one of: {valid_levels}")
        return v.upper()


class NetworkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NETWORK_", **ENV_FILE_CONFIG)

    timeout: float = Field(
        default=3.0, ge=0.1, le=30.0, description="Default (read) timeout in seconds"
    )
    connect_timeout: float = Field(
        default=2.0,
        ge=0.1,
        le=30.0,
        description="TCP connect timeout in seconds; fast-fails unreachable hosts",
    )
    retry_attempts: int = Field(
        default=1,
        ge=0,
        le=10,
        description="Extra discovery attempts for a scanned address that did not answer",
    )
    retry_delay: float = Field(
        default=0.5,
        ge=0.1,
        le=10.0,
        description="Seconds to wait before the next discovery attempt",
    )
    verify_ssl: bool = Field(default=False, description="Verify SSL certificates")


class BackupSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHELLY_BACKUP_", **ENV_FILE_CONFIG)

    scheduler_enabled: bool = Field(
        default=True, description="Run the in-process scheduled-backup poller"
    )
    poll_interval_seconds: int = Field(
        default=60,
        ge=1,
        description="How often the scheduler checks for due backups, in seconds",
    )


class FirmwareSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHELLY_FIRMWARE_", **ENV_FILE_CONFIG)

    dir: str = Field(
        default="./data/firmware",
        description="Directory for cached firmware bundles",
    )
    advertised_base_url: str | None = Field(
        default=None,
        description=(
            "Base URL devices use to reach this API over LAN, "
            "e.g. http://192.168.40.252:8000. Required for local updates; "
            "it cannot be guessed from the server side."
        ),
    )
    index_url: str = Field(
        default="https://updates.shelly.cloud/update",
        description="Shelly firmware index base URL",
    )
    verify_ssl: bool = Field(
        default=False,
        description=(
            "Verify TLS certificates for the firmware index and CDN. Off by "
            "default because Shelly signs updates.shelly.cloud with a private "
            "Allterco CA that no public trust store contains; firmware "
            "integrity is enforced by the device's own signature check."
        ),
    )
    allowed_download_hosts: str = Field(
        default="shelly.cloud",
        description=(
            "Comma separated hosts a firmware bundle may be downloaded from, "
            "matched exactly or as a parent domain, and re-checked on every "
            "redirect. The index names the download URL, and with TLS "
            "verification off that response is worth distrusting, so this "
            "keeps it from pointing the manager at hosts it can reach but the "
            "internet cannot. Set it to * to accept any host; an empty value "
            "keeps the default rather than accepting any."
        ),
    )

    @field_validator("allowed_download_hosts", mode="before")
    @classmethod
    def accept_a_list_of_hosts(cls, value: Any) -> Any:
        """Take the JSON list shape a config file invites as well as a string."""
        if isinstance(value, list | tuple):
            return ",".join(str(host) for host in value)
        return value

    def download_host_allow_list(self) -> list[str]:
        """The hosts firmware may come from, empty meaning any host.

        Kept as a string because a list field can only be set from the
        environment as JSON, and this is a knob operators are invited to set;
        a comma separated value would otherwise stop the app at import. An
        empty value falls back to the default instead of accepting any host,
        so a blank entry in a deployment template cannot quietly turn the
        check off; * is how that is asked for.
        """
        hosts = [
            host.strip().lower()
            for host in self.allowed_download_hosts.split(",")
            if host.strip()
        ]
        if not hosts:
            return ["shelly.cloud"]
        return [] if "*" in hosts else hosts


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHELLY_", **ENV_FILE_CONFIG)

    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    backup: BackupSettings = Field(default_factory=BackupSettings)
    firmware: FirmwareSettings = Field(default_factory=FirmwareSettings)

    config_file: str = Field(
        default="config.json", description="Configuration file path"
    )
    data_dir: str = Field(default="./data", description="Data directory")

    secret_key: str | None = Field(
        default=None,
        description="Secret key for encryption. Must be a valid Fernet key.",
        exclude=True,  # Prevent secret from being logged
    )

    auth_token: str | None = Field(
        default=None,
        description=(
            "Shared auth token gating API + Web UI access. "
            "Unset disables authentication (default)."
        ),
        exclude=True,  # Prevent secret from being logged
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._load_config_file()

    def _load_config_file(self) -> None:
        """Merge the config file over the environment.

        Each section present in the file is rebuilt as its settings class, so
        its values are validated. Unknown keys are ignored.
        """
        config_path = Path(self.config_file)
        if not config_path.is_file():
            return

        try:
            with open(config_path) as f:
                raw = json.load(f)

            if isinstance(raw.get("logging"), dict):
                self.logging = LoggingSettings(**raw["logging"])
            if isinstance(raw.get("network"), dict):
                self.network = NetworkSettings(**raw["network"])
            if isinstance(raw.get("backup"), dict):
                self.backup = BackupSettings(**raw["backup"])
            if isinstance(raw.get("firmware"), dict):
                self.firmware = FirmwareSettings(**raw["firmware"])

            for field_name in ["config_file", "data_dir"]:
                if field_name in raw:
                    setattr(self, field_name, raw[field_name])

        except Exception as e:
            raise ConfigurationError(
                "load_config_file", f"Failed to load config file: {e}"
            ) from e

    def database_path(self) -> str:
        """Get the absolute path to the database file."""
        return os.path.join(self.data_dir, "data.db")


settings = AppSettings()
