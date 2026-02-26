"""Provisioning profile domain entity."""

from dataclasses import dataclass


@dataclass
class ProvisioningProfile:
    """A template for provisioning new Shelly devices."""

    name: str
    wifi_ssid: str | None = None
    wifi_password: str | None = None
    mqtt_enabled: bool = False
    mqtt_server: str | None = None
    mqtt_user: str | None = None
    mqtt_password: str | None = None
    mqtt_topic_prefix_template: str | None = None
    auth_password: str | None = None
    device_name_template: str | None = None
    timezone: str | None = None
    cloud_enabled: bool = False
    is_default: bool = False
    id: int | None = None
    created_at: int | None = None
    updated_at: int | None = None

    def expand_template(
        self, template: str | None, device_info: dict[str, str]
    ) -> str | None:
        """Expand a template string with device info placeholders.

        Supported placeholders: {device_id}, {model}, {app}, {mac}, {mac_suffix}
        """
        if template is None:
            return None

        return template.format(
            device_id=device_info.get("device_id", ""),
            model=device_info.get("model", ""),
            app=device_info.get("app", ""),
            mac=device_info.get("mac", ""),
            mac_suffix=(
                device_info.get("mac", "")[-6:] if device_info.get("mac") else ""
            ),
        )
