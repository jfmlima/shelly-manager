"""
Action definitions for Shelly device operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any
import requests
from .models import ShellyDevice, DeviceStatus
from .network import ShellyRPCClient


class DeviceAction(ABC):
    """Abstract base class for device actions."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, device: ShellyDevice, rpc_client: ShellyRPCClient, 
                auth: Optional[Tuple[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Execute the action on a device."""
        pass


class ListAction(DeviceAction):
    """Action to list/discover devices without any modifications."""
    
    def __init__(self):
        super().__init__("list", "Discover and list Shelly devices")
    
    def execute(self, device: ShellyDevice, rpc_client: ShellyRPCClient, 
                auth: Optional[Tuple[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Just discover the device without any modifications."""
        try:
            result, response_time = rpc_client.make_rpc_request(
                device.ip, "Shelly.GetDeviceInfo", auth=auth
            )
            
            device.response_time = response_time
            device.device_id = result.get('id')
            device.device_type = result.get('model')
            device.device_name = result.get('name')
            device.firmware_version = result.get('fw_id')
            device.status = DeviceStatus.DETECTED

            return {
                "success": True,
                "action": self.name,
                "message": f"Device discovered: {device.device_type}"
            }
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:    
            device.status = DeviceStatus.NOT_SHELLY
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": f"Device not Shelly"
            }    
        except Exception as e:
            device.status = DeviceStatus.ERROR
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": str(e)
            }


class UpdateAction(DeviceAction):
    """Action to check for and apply firmware updates."""
    
    def __init__(self):
        super().__init__("update", "Check for and apply firmware updates")
    
    def execute(self, device: ShellyDevice, rpc_client: ShellyRPCClient, 
                auth: Optional[Tuple[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Check for updates and apply if available."""
        # Get the preferred update channel from kwargs (default to stable)
        preferred_channel = kwargs.get('channel', 'stable').lower()
        if preferred_channel not in ['stable', 'beta']:
            raise ValueError(f"Invalid update channel: {preferred_channel}. Must be 'stable' or 'beta'")
        
        try:
            # First get device info
            result, response_time = rpc_client.make_rpc_request(
                device.ip, "Shelly.GetDeviceInfo", auth=auth
            )
            
            device.response_time = response_time
            device.device_id = result.get('id')
            device.device_type = result.get('model')
            device.device_name = result.get('name')
            device.firmware_version = result.get('fw_id')
            device.status = DeviceStatus.DETECTED
            
            # Check for updates
            update_result, _ = rpc_client.make_rpc_request(
                device.ip, "Shelly.CheckForUpdate", auth=auth
            )
            
            # Ensure update_result is not None
            if not update_result:
                update_result = {}
            
            # Determine which update to apply based on preferred channel
            update_available = False
            update_version = None
            update_channel_used = None
            
            if preferred_channel == 'stable':
                # Only update to stable - no fallback to beta
                stable_update = update_result.get('stable', {})
                
                if stable_update.get('version'):
                    update_available = True
                    update_version = stable_update.get('version')
                    update_channel_used = 'stable'
            
            elif preferred_channel == 'beta':
                # Only update to beta - no fallback to stable
                beta_update = update_result.get('beta', {})
                
                if beta_update.get('version'):
                    update_available = True
                    update_version = beta_update.get('version')
                    update_channel_used = 'beta'
            
            if update_available:
                # Update available - apply it
                try:
                    update_response, _ = rpc_client.make_rpc_request(device.ip, "Shelly.Update", auth=auth)
                    print(f"Update response: {update_response}")  # Debug log
                    # The Shelly.Update call might return None or an empty response
                    # This is normal for update commands
                except Exception as update_error:
                    # Log the update error but don't fail the action
                    device.error_message = f"Update command error: {str(update_error)}"
                
                device.status = DeviceStatus.UPDATED
                return {
                    "success": True,
                    "action": self.name,
                    "message": f"Update started for {device.device_type} (channel: {update_channel_used}, version: {update_version})"
                }
            else:
                device.status = DeviceStatus.NO_UPDATE_NEEDED
                return {
                    "success": True,
                    "action": self.name,
                    "message": f"No update available for {device.device_type} on {preferred_channel} channel"
                }
                
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:    
            device.status = DeviceStatus.NOT_SHELLY
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": f"Device not Shelly"
            }
        except Exception as e:
            device.status = DeviceStatus.ERROR
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": str(e)
            }


class RebootAction(DeviceAction):
    """Action to reboot devices."""
    
    def __init__(self):
        super().__init__("reboot", "Reboot Shelly devices")
    
    def execute(self, device: ShellyDevice, rpc_client: ShellyRPCClient, 
                auth: Optional[Tuple[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Reboot the device."""
        try:
            # First get device info
            result, response_time = rpc_client.make_rpc_request(
                device.ip, "Shelly.GetDeviceInfo", auth=auth
            )
            
            device.response_time = response_time
            device.device_id = result.get('id')
            device.device_type = result.get('model')
            device.device_name = result.get('name')
            device.firmware_version = result.get('fw_id')
            device.status = DeviceStatus.DETECTED
            
            # Reboot the device
            rpc_client.make_rpc_request(device.ip, "Sys.Reboot", auth=auth)
            
            return {
                "success": True,
                "action": self.name,
                "message": f"Reboot initiated for {device.device_type}"
            }
            
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:    
            device.status = DeviceStatus.NOT_SHELLY
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": f"Device not Shelly"
            }
        except Exception as e:
            device.status = DeviceStatus.ERROR
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": str(e)
            }


class ConfigAction(DeviceAction):
    """Action to get or set device configuration."""
    
    def __init__(self, operation: str = "get"):
        self.operation = operation
        name = f"config-{operation}"
        description = f"{'Get' if operation == 'get' else 'Set'} device configuration"
        super().__init__(name, description)
    
    def execute(self, device: ShellyDevice, rpc_client: ShellyRPCClient, 
                auth: Optional[Tuple[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Get or set device configuration."""
        try:
            # First get device info
            result, response_time = rpc_client.make_rpc_request(
                device.ip, "Shelly.GetDeviceInfo", auth=auth
            )
            
            device.response_time = response_time
            device.device_id = result.get('id')
            device.device_type = result.get('model')
            device.device_name = result.get('name')
            device.firmware_version = result.get('fw_id')
            device.status = DeviceStatus.DETECTED
            
            if self.operation == "get":
                config, _ = rpc_client.make_rpc_request(device.ip, "Sys.GetConfig", auth=auth)
                return {
                    "success": True,
                    "action": self.name,
                    "message": f"Configuration retrieved for {device.device_type}",
                    "config": config
                }
            
            elif self.operation == "set":
                config_data = kwargs.get('config', {})
                if not config_data:
                    raise ValueError("No configuration data provided")
                
                rpc_client.make_rpc_request(
                    device.ip, "Sys.SetConfig", 
                    params={"config": config_data}, auth=auth
                )
                return {
                    "success": True,
                    "action": self.name,
                    "message": f"Configuration updated for {device.device_type}"
                }
            
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:    
            device.status = DeviceStatus.NOT_SHELLY
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": f"Device not Shelly"
            }
        except Exception as e:
            device.status = DeviceStatus.ERROR
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": str(e)
            }


class StatusAction(DeviceAction):
    """Action to get detailed device status and available updates."""
    
    def __init__(self):
        super().__init__("status", "Get detailed device status, system information, and available updates")
    
    def execute(self, device: ShellyDevice, rpc_client: ShellyRPCClient, 
                auth: Optional[Tuple[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Get comprehensive device status including update information."""
        try:
            # Get device info
            info_result, response_time = rpc_client.make_rpc_request(
                device.ip, "Shelly.GetDeviceInfo", auth=auth
            )
            
            device.response_time = response_time
            device.device_id = info_result.get('id')
            device.device_type = info_result.get('model')
            device.device_name = info_result.get('name')
            device.firmware_version = info_result.get('fw_id')
            device.status = DeviceStatus.DETECTED
            
            # Get system status
            try:
                status_result, _ = rpc_client.make_rpc_request(
                    device.ip, "Sys.GetStatus", auth=auth
                )
            except:
                status_result = {}

            
            # Check for updates and format the information
            update_info = {"available": False, "details": {}}
            try:
                update_result, _ = rpc_client.make_rpc_request(
                    device.ip, "Shelly.CheckForUpdate", auth=auth
                )
                
                # Parse update information
                if update_result:
                    stable_update = update_result.get('stable', {})
                    beta_update = update_result.get('beta', {})
                    
                    # Check if updates are available
                    current_version = device.firmware_version
                    stable_version = stable_update.get('version') if stable_update else None
                    beta_version = beta_update.get('version') if beta_update else None
                    
                    update_info = {
                        "available": bool(stable_version or beta_version),
                        "current_version": current_version,
                        "raw_response": update_result
                    }
                    
                    # Only add stable_update if stable version exists
                    if stable_version:
                        update_info["stable_update"] = {
                            "available": True,
                            "version": stable_version,
                            "build_id": stable_update.get('build_id'),
                            "build_timestamp": stable_update.get('build_timestamp'),
                            "url": stable_update.get('url')
                        }
                    
                    # Only add beta_update if beta version exists
                    if beta_version:
                        update_info["beta_update"] = {
                            "available": True,
                            "version": beta_version,
                            "build_id": beta_update.get('build_id'),
                            "build_timestamp": beta_update.get('build_timestamp'),
                            "url": beta_update.get('url')
                        }

            except Exception as update_error:
                update_info = {
                    "available": False,
                    "error": str(update_error),
                    "details": {}
                }
            
            # Create status message
            message_parts = [f"Status retrieved for {device.device_type}"]
            if update_info["available"]:
                if "stable_update" in update_info:
                    message_parts.append(f"Stable update available: {update_info['stable_update']['version']}")
                if "beta_update" in update_info:
                    message_parts.append(f"Beta update available: {update_info['beta_update']['version']}")
            else:
                message_parts.append("No updates available")

            return {
                "success": True,
                "action": self.name,
                "message": " | ".join(message_parts),
                "device_info": info_result,
                "system_status": status_result,
                "update_info": update_info
            }
            
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:    
            device.status = DeviceStatus.NOT_SHELLY
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": f"Device not Shelly"
            }
        except Exception as e:
            device.status = DeviceStatus.ERROR
            device.error_message = str(e)
            return {
                "success": False,
                "action": self.name,
                "error": str(e)
            }


# Registry of available actions
AVAILABLE_ACTIONS = {
    "list": ListAction(),
    "update": UpdateAction(),
    "reboot": RebootAction(),
    "config-get": ConfigAction("get"),
    "config-set": ConfigAction("set"),
    "status": StatusAction()
}
