"""
Configuration management for the Shelly Manager application.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.domain.entities.exceptions import ConfigurationError, ValidationError


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
        default=3.0, ge=0.1, le=30.0, description="Default timeout in seconds"
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


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_")

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, ge=1, le=65535, description="API port")
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit: int = Field(default=100, ge=1, description="Rate limit per minute")


class DeviceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEVICE_")

    default_username: str | None = Field(
        default=None, description="Default device username"
    )
    default_password: str | None = Field(
        default=None, description="Default device password"
    )
    update_channel: str = Field(default="stable", description="Default update channel")
    scan_ranges: list[dict[str, str]] = Field(
        default=[{"start": "192.168.1.1", "end": "192.168.1.10"}],
        description="Default scan ranges",
    )

    @field_validator("update_channel")
    @classmethod
    def validate_update_channel(cls, v: str) -> str:
        valid_channels = ["stable", "beta"]
        if v not in valid_channels:
            raise ValueError(
                f"Invalid update channel. Must be one of: {valid_channels}"
            )
        return v


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHELLY_", env_file=".env", env_file_encoding="utf-8"
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    api: APISettings = Field(default_factory=APISettings)
    device: DeviceSettings = Field(default_factory=DeviceSettings)

    config_file: str = Field(
        default="config.json", description="Configuration file path"
    )
    data_dir: str = Field(default="./data", description="Data directory")
    cache_ttl: int = Field(default=300, ge=0, description="Cache TTL in seconds")

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
        if not config_path.exists():
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
            if isinstance(raw.get("device"), dict):
                self.device = DeviceSettings(**raw["device"])

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
                "device": self.device.model_dump(),
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

    def get_device_credentials(self, ip: str) -> dict[str, str] | None:
        if self.device.default_username and self.device.default_password:
            return {
                "username": self.device.default_username,
                "password": self.device.default_password,
            }
        return None

    def get_scan_ranges(self) -> list[dict[str, str]]:
        return self.device.scan_ranges

    def validate_settings(self) -> None:
        try:
            data_path = Path(self.data_dir)
            data_path.mkdir(parents=True, exist_ok=True)

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

        except Exception as e:
            if isinstance(e, (ValidationError | ConfigurationError)):
                raise
            raise ConfigurationError(
                "validate", f"Configuration validation failed: {e}"
            ) from e


settings = AppSettings()
