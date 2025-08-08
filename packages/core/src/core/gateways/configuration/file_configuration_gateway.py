"""
Configuration gateway implementation (read-only for predefined IPs).
"""

import json
import os
from typing import Any

from .configuration import ConfigurationGateway


class FileConfigurationGateway(ConfigurationGateway):

    def __init__(self, config_file_path: str | None = None):
        self._config_file_path = config_file_path or os.path.join(
            os.getcwd(), "config.json"
        )

    async def get_config(self) -> dict[str, Any]:
        try:
            if os.path.exists(self._config_file_path):
                with open(self._config_file_path) as f:
                    config_data: dict[str, Any] = json.load(f)
                    return config_data
            else:
                return self._get_default_config()
        except Exception:
            return self._get_default_config()

    async def get_predefined_ips(self) -> list[str]:
        config = await self.get_config()

        device_ips_set: set[str] = set(config.get("device_ips", []))
        ranges = config.get("predefined_ranges", [])

        for range_config in ranges:
            start_ip = range_config.get("start")
            end_ip = range_config.get("end")

            if start_ip and end_ip:
                start_parts = start_ip.split(".")
                end_parts = end_ip.split(".")

                if len(start_parts) == 4 and len(end_parts) == 4:
                    base_ip = ".".join(start_parts[:3]) + "."
                    start_octet = int(start_parts[3])
                    end_octet = int(end_parts[3])

                    for i in range(start_octet, end_octet + 1):
                        device_ips_set.add(f"{base_ip}{i}")

        return list(device_ips_set)

    def _get_default_config(self) -> dict[str, Any]:
        return {
            "device_ips": [],
            "predefined_ranges": [{"start": "192.168.1.1", "end": "192.168.1.10"}],
            "timeout": 3.0,
            "max_workers": 50,
            "update_channel": "stable",
        }


__all__ = ["FileConfigurationGateway"]
