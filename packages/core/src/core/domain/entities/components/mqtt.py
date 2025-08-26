from typing import Any

from pydantic import Field

from .base import Component


class MqttComponent(Component):
    connected: bool = Field(default=False, description="MQTT connection status")
    enabled: bool = Field(default=False, description="MQTT service enabled")
    server: str | None = Field(None, description="MQTT server address")
    client_id: str | None = Field(None, description="MQTT client ID")
    user: str | None = Field(None, description="MQTT username")
    topic_prefix: str | None = Field(None, description="MQTT topic prefix")
    rpc_notifications: bool = Field(
        default=True, description="RPC notifications enabled"
    )
    status_notifications: bool = Field(
        default=False, description="Status notifications enabled"
    )
    use_client_cert: bool = Field(default=False, description="Use client certificate")
    enable_rpc: bool = Field(default=True, description="Enable RPC over MQTT")
    enable_control: bool = Field(default=True, description="Enable control over MQTT")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "MqttComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            connected=status.get("connected", False),
            enabled=config.get("enable", False),
            server=config.get("server"),
            client_id=config.get("client_id"),
            user=config.get("user"),
            topic_prefix=config.get("topic_prefix"),
            rpc_notifications=config.get("rpc_ntf", True),
            status_notifications=config.get("status_ntf", False),
            use_client_cert=config.get("use_client_cert", False),
            enable_rpc=config.get("enable_rpc", True),
            enable_control=config.get("enable_control", True),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.lower().startswith("mqtt.")]
