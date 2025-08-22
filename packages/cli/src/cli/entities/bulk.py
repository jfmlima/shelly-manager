"""
Bulk operation entities for CLI operations.
"""

from typing import Any

from pydantic import BaseModel, Field

from .common import OperationResult


class BulkOperationRequest(BaseModel):
    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    scan: bool = Field(default=False, description="Scan network for devices")
    ips: str | None = Field(
        default=None, description="Comma-separated list of IP addresses"
    )
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)
    max_concurrent: int = Field(
        default=10, gt=0, le=50, description="Maximum concurrent operations"
    )
    force: bool = Field(default=False, description="Skip confirmation prompts")
    continue_on_error: bool = Field(
        default=True, description="Continue with remaining devices if one fails"
    )
    show_progress: bool = Field(
        default=True, description="Show progress bar during operation"
    )


class BulkRebootRequest(BulkOperationRequest):
    force: bool = Field(default=False, description="Skip confirmation prompt")
    stagger_delay: float = Field(
        default=0.0, ge=0, description="Delay between device reboots in seconds"
    )


class BulkConfigRequest(BulkOperationRequest):
    config_key: str = Field(description="Configuration key to modify")
    config_value: Any = Field(description="Value to set")
    create_backup: bool = Field(
        default=True, description="Create backup before modifying configuration"
    )
    validate_before: bool = Field(
        default=True, description="Validate configuration before applying"
    )


class BulkCommandRequest(BulkOperationRequest):
    command: str = Field(description="Command to execute on devices")
    command_args: dict[str, Any] = Field(
        default_factory=dict, description="Arguments to pass with the command"
    )
    expected_response: str | None = Field(
        default=None, description="Expected response pattern for validation"
    )


class BulkOperationResult(OperationResult):
    total_devices: int = Field(default=0)
    successful_operations: int = Field(default=0)
    failed_operations: int = Field(default=0)
    device_results: dict[str, OperationResult] = Field(
        default_factory=dict,
        description="Individual results for each device (IP -> result)",
    )
    operation_type: str = Field(description="Type of bulk operation performed")
    time_taken_seconds: float | None = Field(default=None)
    errors_by_device: dict[str, str] = Field(
        default_factory=dict, description="Error messages by device IP"
    )


class BulkRebootResult(BulkOperationResult):
    operation_type: str = Field(default="bulk_reboot")
    stagger_delay_used: float = Field(default=0.0)
    reboot_order: list[str] = Field(
        default_factory=list, description="Order in which devices were rebooted"
    )


class BulkConfigResult(BulkOperationResult):
    operation_type: str = Field(default="bulk_config")
    config_key: str = Field(description="Configuration key that was modified")
    config_value: Any = Field(description="Value that was set")
    backups_created: dict[str, str] = Field(
        default_factory=dict,
        description="Backup files created for each device (IP -> backup_path)",
    )
    validation_errors: dict[str, list[str]] = Field(
        default_factory=dict, description="Validation errors by device IP"
    )


class BulkCommandResult(BulkOperationResult):
    operation_type: str = Field(default="bulk_command")
    command: str = Field(description="Command that was executed")
    command_responses: dict[str, Any] = Field(
        default_factory=dict, description="Responses from each device (IP -> response)"
    )
    validation_failures: list[str] = Field(
        default_factory=list, description="Devices that didn't return expected response"
    )


class BulkConfigExportRequest(BulkOperationRequest):
    component_types: list[str] = Field(
        description="Component types to export (e.g., switch, input)"
    )
    output_file: str = Field(description="Output file path for exported configuration")


class BulkConfigApplyRequest(BulkOperationRequest):
    component_type: str = Field(description="Single component type to apply config to")
    config_file: str | None = Field(
        default=None, description="Path to configuration file"
    )
    config_data: dict[str, Any] | None = Field(
        default=None, description="Configuration data directly"
    )


class BulkConfigExportResult(BulkOperationResult):
    operation_type: str = Field(default="bulk_config_export")
    component_types: list[str] = Field(description="Component types that were exported")
    output_file: str = Field(description="File where configuration was saved")
    devices_exported: int = Field(default=0, description="Number of devices exported")


class BulkConfigApplyResult(BulkOperationResult):
    operation_type: str = Field(default="bulk_config_apply")
    component_type: str = Field(description="Component type that was configured")
    config_source: str = Field(description="Source of configuration (file or direct)")
    components_configured: int = Field(
        default=0, description="Number of components configured"
    )
