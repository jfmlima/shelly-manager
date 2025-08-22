"""
Response models for API serialization.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DeviceResponse(BaseModel):

    ip: str
    device_id: str | None = None
    device_type: str | None = None
    device_name: str | None = None
    firmware_version: str | None = None
    status: str
    response_time: float | None = None
    error_message: str | None = None
    last_seen: datetime | None = None


class UpdateInfoResponse(BaseModel):

    available: bool = False
    current_version: str | None = None
    stable_version: str | None = None
    beta_version: str | None = None
    stable_details: dict[str, Any] | None = None
    beta_details: dict[str, Any] | None = None


class DeviceStatusResponse(DeviceResponse):

    update_info: UpdateInfoResponse | None = None
    system_status: dict[str, Any] | None = None
    device_info: dict[str, Any] | None = None


class ActionResultResponse(BaseModel):

    success: bool
    action_type: str
    device_ip: str
    message: str
    data: dict[str, Any] | None = None
    error: str | None = None
    timestamp: datetime


class ScanResultResponse(BaseModel):

    devices: list[DeviceResponse]
    total_scanned: int
    devices_found: int
    scan_duration: float
    timestamp: datetime


class BulkActionResultResponse(BaseModel):

    results: list[ActionResultResponse]
    total_devices: int
    successful_actions: int
    failed_actions: int
    timestamp: datetime


class ConfigurationResponse(BaseModel):

    schema_version: str
    description: str
    predefined_ips: list[str]
    default_credentials: dict[str, str]
    scan_settings: dict[str, Any]
    export_settings: dict[str, Any]


class ActionHistoryResponse(BaseModel):

    actions: list[ActionResultResponse]
    total_count: int
    page: int
    limit: int


class HealthCheckResponse(BaseModel):

    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
    uptime_seconds: float


class ErrorResponse(BaseModel):

    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str | None = None


class BulkExportConfigResponse(BaseModel):
    export_metadata: dict[str, Any] = Field(
        ..., description="Export metadata including timestamp and device count"
    )
    devices: dict[str, Any] = Field(
        ..., description="Configuration data organized by device IP"
    )


class BulkApplyConfigResponse(BaseModel):
    ip: str
    component_key: str
    success: bool
    message: str
    error: str | None = None
