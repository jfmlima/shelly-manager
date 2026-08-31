"""
Configuration management for the Shelly Manager application.
"""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.domain.entities.exceptions import ConfigurationError, ValidationError

MISSING_SECRET_KEY_MESSAGE = (
    "SHELLY_SECRET_KEY is not set. Generate one with: "
    "openssl rand -base64 32 | tr '+/' '-_'"
)

INVALID_SECRET_KEY_MESSAGE = (
    "SHELLY_SECRET_KEY is not a valid Fernet key. Generate one with: "
    "openssl rand -base64 32 | tr '+/' '-_'."
)


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_")

    url: str = Field(default="sqlite:///shelly_manager.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQL echo")


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="json", description="Log format (json or console)")
    file_path: str | None = Field(default=None, description="Log file path")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid logging level. Must be one of: {valid_levels}")
        return v.upper()

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        valid_formats = ["json", "console"]
        if v not in valid_formats:
            raise ValueError(f"Invalid log format. Must be one of: {valid_formats}")
        return v


class NetworkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NETWORK_")

    timeout: float = Field(
        default=3.0, ge=0.1, le=30.0, description="Default (read) timeout in seconds"
    )
    connect_timeout: float = Field(
        default=2.0,
        ge=0.1,
        le=30.0,
        description="TCP connect timeout in seconds; fast-fails unreachable hosts",
    )
    max_workers: int = Field(
        default=50, ge=1, le=200, description="Maximum concurrent workers"
    )
    retry_attempts: int = Field(
        default=3, ge=0, le=10, description="Number of retry attempts"
    )
    retry_delay: float = Field(
        default=1.0, ge=0.1, le=10.0, description="Delay between retries"
    )
    verify_ssl: bool = Field(default=False, description="Verify SSL certificates")


class BackupSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHELLY_BACKUP_")

    scheduler_enabled: bool = Field(
        default=True, description="Run the in-process scheduled-backup poller"
    )
    poll_interval_seconds: int = Field(
        default=60,
        ge=1,
        description="How often the scheduler checks for due backups, in seconds",
    )


class FirmwareSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHELLY_FIRMWARE_")

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


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_")

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(
        default=int(os.getenv("PORT", "8000")), ge=1, le=65535, description="API port"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit: int = Field(default=100, ge=1, description="Rate limit per minute")


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHELLY_", env_file=".env", env_file_encoding="utf-8"
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    api: APISettings = Field(default_factory=APISettings)
    backup: BackupSettings = Field(default_factory=BackupSettings)
    firmware: FirmwareSettings = Field(default_factory=FirmwareSettings)

    config_file: str = Field(
        default="config.json", description="Configuration file path"
    )
    data_dir: str = Field(default="./data", description="Data directory")
    cache_ttl: int = Field(default=300, ge=0, description="Cache TTL in seconds")

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
        """Load and merge external config file safely with validation.

        The previous implementation assigned values directly via setattr which could
        bypass pydantic validation for nested models. This version reconstructs
        sub-settings objects when corresponding sections are provided and only
        applies known fields. Unknown top-level keys are ignored (could be logged
        in future for transparency).
        """
        config_path = Path(self.config_file)
        if not config_path.is_file():
            return

        try:
            with open(config_path) as f:
                raw = json.load(f)

            if isinstance(raw.get("database"), dict):
                self.database = DatabaseSettings(**raw["database"])
            if isinstance(raw.get("logging"), dict):
                self.logging = LoggingSettings(**raw["logging"])
            if isinstance(raw.get("network"), dict):
                self.network = NetworkSettings(**raw["network"])
            if isinstance(raw.get("api"), dict):
                self.api = APISettings(**raw["api"])
            if isinstance(raw.get("backup"), dict):
                self.backup = BackupSettings(**raw["backup"])
            if isinstance(raw.get("firmware"), dict):
                self.firmware = FirmwareSettings(**raw["firmware"])

            for field_name in ["config_file", "data_dir", "cache_ttl"]:
                if field_name in raw:
                    setattr(self, field_name, raw[field_name])

        except Exception as e:
            raise ConfigurationError(
                "load_config_file", f"Failed to load config file: {e}"
            ) from e

    def save_config(self) -> None:
        try:
            config_data = {
                "database": self.database.model_dump(),
                "logging": self.logging.model_dump(),
                "network": self.network.model_dump(),
                "api": self.api.model_dump(),
                "backup": self.backup.model_dump(),
                "firmware": self.firmware.model_dump(),
                "config_file": self.config_file,
                "data_dir": self.data_dir,
                "cache_ttl": self.cache_ttl,
            }

            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            raise ConfigurationError(
                "save_config", f"Failed to save config: {e}"
            ) from e

    def validate_settings(self) -> None:
        try:
            data_path = Path(self.data_dir)
            data_path.mkdir(parents=True, exist_ok=True)

            firmware_path = Path(self.firmware.dir)
            firmware_path.mkdir(parents=True, exist_ok=True)

            if self.network.timeout <= 0:
                raise ValidationError(
                    "timeout", self.network.timeout, "Timeout must be positive"
                )

            if self.network.max_workers <= 0:
                raise ValidationError(
                    "max_workers",
                    self.network.max_workers,
                    "Max workers must be positive",
                )

            if self.api.port < 1 or self.api.port > 65535:
                raise ValidationError(
                    "port", self.api.port, "Port must be between 1 and 65535"
                )

            if self.secret_key is None:
                raise ValidationError(
                    "secret_key",
                    None,
                    MISSING_SECRET_KEY_MESSAGE,
                )

            # Validate secret key format (Fernet)
            try:
                from cryptography.fernet import Fernet

                Fernet(self.secret_key.encode())
            except Exception as e:
                raise ValidationError(
                    "secret_key",
                    "***",
                    f"Invalid SHELLY_SECRET_KEY. Must be a valid Fernet key. Error: {e}",
                ) from e

        except Exception as e:
            if isinstance(e, (ValidationError | ConfigurationError)):
                raise
            raise ConfigurationError(
                "validate", f"Configuration validation failed: {e}"
            ) from e

    def database_path(self) -> str:
        """Get the absolute path to the database file."""
        return os.path.join(self.data_dir, "data.db")


settings = AppSettings()
