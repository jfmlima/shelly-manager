from typing import Any

from pydantic import Field

from .base import Component


class BluetoothLEComponent(Component):

    enabled: bool = Field(default=False, description="Bluetooth LE enabled")
    rpc_enabled: bool = Field(default=False, description="RPC over BLE enabled")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "BluetoothLEComponent":
        base = Component.from_raw_data(component_data)
        config = component_data.get("config", {})

        rpc_config = config.get("rpc", {})

        return cls(
            **base.model_dump(),
            enabled=config.get("enable", False),
            rpc_enabled=rpc_config.get("enable", False),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("BLE.")]
