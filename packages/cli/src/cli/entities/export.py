"""
Export-related entities for CLI operations.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .common import OperationResult


class ExportRequest(BaseModel):
    """Request for exporting device configurations."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    output_dir: str = Field(
        default="exports", description="Directory to save exported configurations"
    )
    format: str = Field(
        default="json",
        pattern=r"^(json|yaml)$",
        description="Export format (json or yaml)",
    )
    include_status: bool = Field(
        default=True, description="Include device status information"
    )
    include_metadata: bool = Field(
        default=True, description="Include export metadata (timestamp, version, etc.)"
    )
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)
    overwrite: bool = Field(
        default=False, description="Overwrite existing export files"
    )
    output: str | None = Field(default=None, description="Output file path")
    force: bool = Field(default=False, description="Force overwrite without prompt")
    include_config: bool = Field(
        default=True, description="Include device configuration"
    )
    scan: bool = Field(default=False, description="Scan network for devices")
    ips: list[str] | None = Field(
        default=None, description="List of device IP addresses"
    )
    pretty: bool = Field(default=False, description="Pretty print output")
    network: str | None = Field(default=None, description="Network range to scan")

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: str) -> str:
        try:
            Path(v)
            return v
        except Exception as e:
            raise ValueError(f"Invalid output directory path: {v}") from e


class BackupRequest(BaseModel):
    """Request for backing up device configurations."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    backup_dir: str = Field(
        default="backups", description="Directory to save backup files"
    )
    include_timestamp: bool = Field(
        default=True, description="Include timestamp in backup filenames"
    )
    compress: bool = Field(default=False, description="Compress backup files")
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)
    retention_days: int | None = Field(
        default=None,
        ge=1,
        description="Number of days to keep backups (None = keep all)",
    )

    @field_validator("backup_dir")
    @classmethod
    def validate_backup_dir(cls, v: str) -> str:
        try:
            Path(v)
            return v
        except Exception as e:
            raise ValueError(f"Invalid backup directory path: {v}") from e


class RestoreRequest(BaseModel):
    """Request for restoring device configurations."""

    device: str = Field(description="IP address of device to restore")
    backup_file: str = Field(description="Path to backup file")
    force: bool = Field(default=False, description="Skip confirmation prompt")
    create_backup: bool = Field(
        default=True, description="Create backup before restore"
    )
    timeout: float = Field(default=3.0, gt=0)

    @field_validator("backup_file")
    @classmethod
    def validate_backup_file(cls, v: str) -> str:
        backup_path = Path(v)
        if not backup_path.exists():
            raise ValueError(f"Backup file does not exist: {v}")
        if not backup_path.is_file():
            raise ValueError(f"Backup path is not a file: {v}")
        return v


class ExportResult(OperationResult):
    """Result of an export operation."""

    exported_files: list[str] = Field(default_factory=list)
    export_dir: str = Field(description="Directory where files were exported")
    total_devices: int = Field(default=0)
    successful_exports: int = Field(default=0)
    failed_exports: int = Field(default=0)
    export_format: str = Field(description="Format used for export")
    metadata_included: bool = Field(default=False)


class BackupResult(OperationResult):
    """Result of a backup operation."""

    backup_files: list[str] = Field(default_factory=list)
    backup_dir: str = Field(description="Directory where backups were saved")
    total_devices: int = Field(default=0)
    successful_backups: int = Field(default=0)
    failed_backups: int = Field(default=0)
    compressed: bool = Field(default=False)
    cleanup_performed: bool = Field(
        default=False, description="Whether old backups were cleaned up"
    )
    cleaned_files: list[str] = Field(default_factory=list)


class RestoreResult(OperationResult):
    """Result of a restore operation."""

    restore_successful: bool = Field(default=False)
    backup_created: bool = Field(default=False)
    backup_file: str | None = Field(default=None)
    restored_from: str = Field(description="Path of backup file used")
    configuration_changes: dict[str, Any] = Field(
        default_factory=dict, description="Summary of configuration changes made"
    )
