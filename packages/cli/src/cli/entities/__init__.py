"""
CLI entities using Pydantic for validation and serialization.

This module contains all data classes, requests, and response models
used throughout the CLI application, enhanced with Pydantic for
type safety and validation.
"""

from .bulk import *  # noqa: F403
from .common import *  # noqa: F403
from .component_actions import *  # noqa: F403
from .device import *  # noqa: F403
from .export import *  # noqa: F403

__all__ = [
    # Common entities
    "DeviceDiscoveryRequest",  # noqa: F405
    "OperationResult",  # noqa: F405
    # Device entities
    "DeviceScanRequest",  # noqa: F405
    "DeviceStatusRequest",  # noqa: F405
    # Component action entities
    "ComponentActionRequest",  # noqa: F405
    "ComponentActionResult",  # noqa: F405
    "ComponentActionsListRequest",  # noqa: F405
    "ComponentActionsListResult",  # noqa: F405
    # Export entities
    "ExportRequest",  # noqa: F405
    # Bulk operation entities
    "BulkOperationRequest",  # noqa: F405
    "BulkConfigExportRequest",  # noqa: F405
    "BulkConfigApplyRequest",  # noqa: F405
]
