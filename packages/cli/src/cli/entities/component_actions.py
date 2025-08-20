"""
Component actions entities for CLI operations.
"""

from typing import Any

from pydantic import BaseModel, Field

from .common import OperationResult


class ComponentActionRequest(BaseModel):
    """Request for executing component actions via CLI."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    component_key: str = Field(
        ..., description="Component key (e.g., 'switch:0', 'sys')"
    )
    action: str = Field(..., description="Action (e.g., 'Toggle', 'Reboot')")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific parameters (e.g., {'channel': 'beta', 'output': True})",
    )
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)
    force: bool = Field(default=False)


class ComponentActionResult(OperationResult):
    """Result of component action operation."""

    component_key: str = Field(..., description="Component that action was executed on")
    action: str = Field(..., description="Action that was executed")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Parameters used for the action"
    )
    action_successful: bool = Field(default=False)
    action_data: dict[str, Any] | None = Field(default=None)


class ComponentActionsListRequest(BaseModel):
    """Request for listing component actions."""

    devices: list[str] = Field(default_factory=list)
    from_config: bool = Field(default=False)
    timeout: float = Field(default=3.0, gt=0)
    workers: int = Field(default=10, gt=0, le=50)
    component_type: str | None = Field(
        default=None, description="Filter by component type"
    )


class ComponentActionsListResult(OperationResult):
    """Result of listing component actions."""

    available_actions: dict[str, list[str]] = Field(default_factory=dict)


__all__ = [
    "ComponentActionRequest",
    "ComponentActionResult",
    "ComponentActionsListRequest",
    "ComponentActionsListResult",
]
