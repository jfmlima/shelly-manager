import logging
from typing import Any

from pydantic import ValidationError

from .base import Component
from .registry import model_for

logger = logging.getLogger(__name__)


class ComponentFactory:
    @staticmethod
    def create_component(component_data: dict[str, Any]) -> Component:
        key = component_data.get("key", "")
        component_type = key.split(":")[0] if ":" in key else key

        try:
            return model_for(component_type).from_raw_data(component_data)
        except ValidationError as e:
            logger.warning(
                "Component %s did not match its typed model, keeping raw data: %s",
                key,
                e,
            )
            return Component.from_raw_data(component_data)

    @staticmethod
    def create_component_from_status(
        key: str, status_data: dict[str, Any]
    ) -> Component:
        component_data = {"key": key, "status": status_data, "config": {}, "attrs": {}}
        return ComponentFactory.create_component(component_data)
