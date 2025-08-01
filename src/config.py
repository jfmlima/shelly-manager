"""
Configuration settings for Shelly device manager.
"""

import json
import os
from typing import List, Optional, Dict, Any

# Default scan settings
DEFAULT_TIMEOUT = 3
DEFAULT_MAX_WORKERS = 50
DEFAULT_VERIFY_SSL = False

# Network settings
MIN_OCTET = 1
MAX_OCTET = 254
MIN_WORKERS = 1
MAX_WORKERS = 200

# Configuration file settings
DEFAULT_CONFIG_FILE = "shelly_config.json"
CONFIG_SCHEMA_VERSION = "1.0"

# RPC settings
RPC_ID = 1
USER_AGENT = 'ShellyScanner/1.0'
CONTENT_TYPE = 'application/json'

# Shelly RPC methods
SHELLY_METHODS = {
    'get_device_info': 'Shelly.GetDeviceInfo',
    'check_for_update': 'Shelly.CheckForUpdate',
    'update': 'Shelly.Update',
    'get_config': 'Sys.GetConfig',
    'set_config': 'Sys.SetConfig',
    'reboot': 'Sys.Reboot'
}

# Export settings
DEFAULT_EXPORT_FORMATS = ['json', 'csv']
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Logging settings
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Status icons for display
STATUS_ICONS = {
    'DETECTED': "✓",
    'UPDATED': "↑",
    'NO_UPDATE_NEEDED': "•",
    'AUTH_REQUIRED': "🔒",
    'NOT_SHELLY': "✗",
    'UNREACHABLE': "-",
    'ERROR': "!"
}


class ConfigManager:
    """Manages configuration file loading and validation."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.config_data = {}
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from file if it exists."""
        if not os.path.exists(self.config_file):
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                self.config_data = json.load(f)
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")
            return False
    
    def get_predefined_ips(self) -> List[str]:
        """Get list of predefined IP addresses from config."""
        return self.config_data.get('predefined_ips', [])
    
    def get_default_credentials(self) -> Optional[Dict[str, str]]:
        """Get default credentials from config."""
        return self.config_data.get('default_credentials')
    
    def get_scan_settings(self) -> Dict[str, Any]:
        """Get scan settings from config."""
        return self.config_data.get('scan_settings', {})
    
    def get_update_settings(self) -> Dict[str, Any]:
        """Get update settings from config."""
        return self.config_data.get('update_settings', {})
    
    def has_predefined_ips(self) -> bool:
        """Check if predefined IPs are configured."""
        return bool(self.get_predefined_ips())
    
    def create_sample_config(self, filename: Optional[str] = None) -> str:
        """Create a sample configuration file."""
        config_file = filename or DEFAULT_CONFIG_FILE
        
        sample_config = {
            "schema_version": CONFIG_SCHEMA_VERSION,
            "description": "Shelly device manager configuration",
            "predefined_ips": [
                "192.168.1.100",
                "192.168.1.101",
                "192.168.1.102"
            ],
            "default_credentials": {
                "username": "admin",
                "password": "your_password_here"
            },
            "scan_settings": {
                "timeout": DEFAULT_TIMEOUT,
                "max_workers": DEFAULT_MAX_WORKERS,
                "verify_ssl": DEFAULT_VERIFY_SSL
            },
            "update_settings": {
                "default_channel": "stable",
                "auto_reboot": False
            },
            "export_settings": {
                "default_format": "json",
                "auto_timestamp": True
            }
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(sample_config, f, indent=2)
            return config_file
        except IOError as e:
            raise IOError(f"Could not create config file {config_file}: {e}")


# Global config manager instance
_config_manager = None

def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """Get or create the global config manager."""
    global _config_manager
    if _config_manager is None or config_file:
        _config_manager = ConfigManager(config_file)
    return _config_manager
