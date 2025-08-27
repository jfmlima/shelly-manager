from typing import Any

from pydantic import Field

from .base import Component


class WifiComponent(Component):
    sta_ip: str | None = Field(None, description="Station IP address")
    sta_ip6: list[str] | None = Field(None, description="IPv6 addresses")
    wifi_status: str = Field(default="unknown", description="WiFi connection status")
    ssid: str | None = Field(None, description="Connected SSID")
    bssid: str | None = Field(None, description="Connected BSSID")
    rssi: int = Field(default=0, description="Signal strength in dBm")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "WifiComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})

        return cls(
            **base.model_dump(),
            sta_ip=status.get("sta_ip"),
            sta_ip6=status.get("sta_ip6", []),
            wifi_status=status.get("status", "unknown"),
            ssid=status.get("ssid"),
            bssid=status.get("bssid"),
            rssi=status.get("rssi", 0),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("Wifi.")]
