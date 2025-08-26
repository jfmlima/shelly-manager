from typing import Any

from pydantic import Field

from .base import Component


class EthernetComponent(Component):
    eth_ip: str | None = Field(None, description="Ethernet IP address")
    eth_ip6: list[str] = Field(default_factory=list, description="IPv6 addresses")
    enabled: bool = Field(default=True, description="Ethernet interface enabled")
    server_mode: bool = Field(default=False, description="Server mode enabled")
    ipv4_mode: str = Field(default="dhcp", description="IPv4 configuration mode")
    netmask: str | None = Field(None, description="Network mask")
    gateway: str | None = Field(None, description="Gateway address")
    nameserver: str | None = Field(None, description="DNS nameserver")

    @classmethod
    def from_raw_data(cls, component_data: dict[str, Any]) -> "EthernetComponent":
        base = Component.from_raw_data(component_data)
        status = component_data.get("status", {})
        config = component_data.get("config", {})

        return cls(
            **base.model_dump(),
            eth_ip=status.get("ip"),
            eth_ip6=status.get("ip6", []),
            enabled=config.get("enable", True),
            server_mode=config.get("server_mode", False),
            ipv4_mode=config.get("ipv4mode", "dhcp"),
            netmask=config.get("netmask"),
            gateway=config.get("gw"),
            nameserver=config.get("nameserver"),
        )

    def get_available_actions(self, all_methods: list[str]) -> list[str]:
        return [m for m in all_methods if m.startswith("Eth.")]
