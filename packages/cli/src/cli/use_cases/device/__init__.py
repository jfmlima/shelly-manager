"""
Device use cases for CLI operations.
"""

from .config_update import ConfigUpdateUseCase
from .firmware_update import FirmwareUpdateUseCase

__all__ = [
    "FirmwareUpdateUseCase",
    "ConfigUpdateUseCase",
]
