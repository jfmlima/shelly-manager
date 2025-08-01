"""
Shelly device manager package.
"""

from .models import DeviceStatus, ShellyDevice
from .scanner import ShellyScanner, DeviceManager
from .network import NetworkUtils, ShellyRPCClient
from .exporter import ResultsExporter
from .ui import DisplayUtils
from .cli import CLI
from .actions import DeviceAction, AVAILABLE_ACTIONS
from . import config

__version__ = "1.0.0"
__all__ = [
    "DeviceStatus",
    "ShellyDevice", 
    "ShellyScanner",
    "DeviceManager",
    "NetworkUtils",
    "ShellyRPCClient",
    "ResultsExporter",
    "DisplayUtils",
    "CLI",
    "DeviceAction",
    "AVAILABLE_ACTIONS",
    "config"
]
