"""
Configuration-related entities for CLI operations.
"""

from typing import Any

from pydantic import BaseModel, Field

from .common import OperationResult


class ConfigShowRequest(BaseModel):
    """Request for showing configuration."""

    section: str | None = Field(default=None)
    key: str | None = Field(default=None)
    format: str = Field(
        default="yaml",
        pattern=r"^(yaml|json|table)$",
        description="Output format (yaml, json, or table)",
    )


class ConfigSetRequest(BaseModel):
    """Request for setting configuration values."""

    data: str = Field(description="JSON configuration data to set")
    force: bool = Field(default=False, description="Skip confirmation prompt")
    key: str | None = Field(
        default=None, description="Specific configuration key to set"
    )
    value: Any | None = Field(default=None, description="Value to set for specific key")
    section: str | None = Field(default=None)
    create_section: bool = Field(
        default=True, description="Create section if it doesn't exist"
    )


class ConfigValidateRequest(BaseModel):
    """Request for validating configuration."""

    config_path: str | None = Field(
        default=None, description="Path to config file, defaults to active config"
    )
    check_devices: bool = Field(
        default=True, description="Whether to ping devices listed in config"
    )
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=20, gt=0, le=100)


class ConfigInitRequest(BaseModel):
    """Request for initializing configuration."""

    config_path: str | None = Field(
        default=None, description="Path where to create config file"
    )
    force: bool = Field(default=False, description="Overwrite existing configuration")
    include_examples: bool = Field(
        default=True, description="Include example configurations"
    )


class ConfigShowResult(OperationResult):
    """Result of showing configuration."""

    config_data: dict[str, Any] = Field(default_factory=dict)
    formatted_output: str = Field(default="")
    config_path: str | None = Field(default=None)


class ConfigSetResult(OperationResult):
    """Result of setting configuration."""

    previous_value: Any | None = Field(default=None)
    new_value: Any = Field(description="The value that was set")
    config_path: str = Field(description="Path to the modified config file")


class ConfigValidateResult(OperationResult):
    """Result of configuration validation."""

    is_valid: bool = Field(default=False)
    validation_errors: list[str] = Field(default_factory=list)
    device_status: dict[str, bool] = Field(
        default_factory=dict, description="Device IP -> reachability status"
    )
    unreachable_devices: list[str] = Field(default_factory=list)


class ConfigInitResult(OperationResult):
    """Result of configuration initialization."""

    config_path: str = Field(description="Path to the created config file")
    config_created: bool = Field(default=False)
    examples_included: bool = Field(default=False)
