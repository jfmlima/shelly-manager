"""Device gateway implementations."""

from .device import DeviceGateway
from .shelly_device_gateway import ShellyDeviceGateway

__all__ = [
    "DeviceGateway",
    "ShellyDeviceGateway",
]
