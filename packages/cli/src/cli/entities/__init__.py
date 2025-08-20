"""
CLI entities using Pydantic for validation and serialization.

This module contains all data classes, requests, and response models
used throughout the CLI application, enhanced with Pydantic for
type safety and validation.
"""

from .bulk import *  # noqa: F403
from .common import *  # noqa: F403
from .component_actions import *  # noqa: F403
from .config import *  # noqa: F403
from .device import *  # noqa: F403
from .export import *  # noqa: F403
from .update import *  # noqa: F403

__all__ = [
    # Common entities
    "DeviceDiscoveryRequest",  # noqa: F405
    "OperationResult",  # noqa: F405
    # Device entities
    "DeviceScanRequest",  # noqa: F405
    "DeviceStatusRequest",  # noqa: F405
    "DeviceStatusResult",  # noqa: F405
    # Component action entities
    "ComponentActionRequest",  # noqa: F405
    "ComponentActionResult",  # noqa: F405
    "ComponentActionsListRequest",  # noqa: F405
    "ComponentActionsListResult",  # noqa: F405
    # Config entities
    "ConfigShowRequest",  # noqa: F405
    "ConfigSetRequest",  # noqa: F405
    "ConfigValidateRequest",  # noqa: F405
    "ConfigInitRequest",  # noqa: F405
    "ConfigShowResult",  # noqa: F405
    "ConfigSetResult",  # noqa: F405
    "ConfigValidateResult",  # noqa: F405
    "ConfigInitResult",  # noqa: F405
    # Export entities
    "ExportRequest",  # noqa: F405
    "BackupRequest",  # noqa: F405
    "RestoreRequest",  # noqa: F405
    "ExportResult",  # noqa: F405
    "BackupResult",  # noqa: F405
    "RestoreResult",  # noqa: F405
    # Bulk operation entities
    "BulkOperationRequest",  # noqa: F405
    "BulkRebootRequest",  # noqa: F405
    "BulkConfigRequest",  # noqa: F405
    "BulkCommandRequest",  # noqa: F405
    "BulkOperationResult",  # noqa: F405
    "BulkRebootResult",  # noqa: F405
    "BulkConfigResult",  # noqa: F405
    "BulkCommandResult",  # noqa: F405
]
