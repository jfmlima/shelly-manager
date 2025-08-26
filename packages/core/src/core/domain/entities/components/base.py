from typing import Any

from pydantic import BaseModel, Field


class Component(BaseModel):
    key: str = Field(
        ..., description="Component key (e.g., 'switch:0', 'input:0', 'sys')"
    )
    component_type: str = Field(
        ..., description="Component type (e.g., 'switch', 'input', 'cover')"
    )
    component_id: int | None = Field(
        None, description="Component ID (None for system components)"
    )
    status: dict[str, Any] = Field(default_factory=dict, description="Raw status data")
    config: dict[str, Any] = Field(default_factory=dict, description="Raw config data")
    attrs: dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )
    available_actions: list[str] = Field(
        default_factory=list, description="Available actions for this component"
    )

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "Component":
        key = component_data.get("key", "")
        component_type = key.split(":")[0] if ":" in key else key
        component_id = None

        if ":" in key:
            try:
                component_id = int(key.split(":")[1])
            except (IndexError, ValueError):
                pass

        return cls(
            key=key,
            component_type=component_type,
            component_id=component_id,
            status=component_data.get("status", {}),
            config=component_data.get("config", {}),
            attrs=component_data.get("attrs", {}),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [
            m
            for m in all_methods
            if m.lower().startswith(self.component_type.lower() + ".")
        ]

    def can_perform_action(self, action: str) -> bool:
        component_prefix = self.component_type.title()
        expected_method = f"{component_prefix}.{action}"

        return expected_method in self.available_actions
