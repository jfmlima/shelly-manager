"""
Device management and scanning functionality with action-based operations.
"""

import logging
import sys
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import concurrent.futures

from .models import DeviceStatus, ShellyDevice
from .network import NetworkUtils, ShellyRPCClient
from .actions import DeviceAction, AVAILABLE_ACTIONS


class DeviceManager:
    """Manages individual Shelly device operations using actions."""
    
    def __init__(self, rpc_client: ShellyRPCClient, logger: logging.Logger):
        self.rpc_client = rpc_client
        self.logger = logger
    
    def execute_action(self, ip: str, action: DeviceAction, 
                      auth: Optional[Tuple[str, str]] = None, **kwargs) -> Tuple[ShellyDevice, Dict]:
        """Execute an action on a device."""
        device = ShellyDevice(ip=ip, status=DeviceStatus.UNREACHABLE)
        
        try:
            result = action.execute(device, self.rpc_client, auth=auth, **kwargs)
            
            if result["success"]:
                device.last_seen = datetime.now().isoformat()
            
            return device, result
            
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 401:
                device.status = DeviceStatus.AUTH_REQUIRED
                device.auth_required = True
                self.logger.info(f"{ip}: Authentication required")
                return device, {
                    "success": False,
                    "action": action.name,
                    "error": "Authentication required"
                }
            elif e.response and e.response.status_code == 404:
                device.status = DeviceStatus.NOT_SHELLY
                self.logger.debug(f"{ip}: Not a Shelly device (404)")
                return device, {
                    "success": False,
                    "action": action.name,
                    "error": "Not a Shelly device"
                }
            else:
                device.status = DeviceStatus.ERROR
                device.error_message = f"HTTP {e.response.status_code if e.response else 'Unknown'}"
                self.logger.warning(f"{ip}: HTTP error {device.error_message}")
                return device, {
                    "success": False,
                    "action": action.name,
                    "error": device.error_message
                }
                
        except requests.exceptions.ConnectionError:
            device.status = DeviceStatus.UNREACHABLE
            self.logger.debug(f"{ip}: No device detected")
            return device, {
                "success": False,
                "action": action.name,
                "error": "Device unreachable"
            }
            
        except requests.exceptions.Timeout:
            device.status = DeviceStatus.ERROR
            device.error_message = "Timeout"
            self.logger.warning(f"{ip}: Request timeout")
            return device, {
                "success": False,
                "action": action.name,
                "error": "Request timeout"
            }
            
        except Exception as e:
            device.status = DeviceStatus.ERROR
            device.error_message = str(e)
            self.logger.error(f"{ip}: Unexpected error: {e}")
            return device, {
                "success": False,
                "action": action.name,
                "error": str(e)
            }


class ShellyScanner:
    """Production-ready Shelly device scanner with action-based operations."""
    
    def __init__(self, timeout: int = 3, max_workers: int = 50, 
                 verbose: bool = False, verify_ssl: bool = False):
        self.timeout = timeout
        self.max_workers = max_workers
        self.verify_ssl = verify_ssl
        self.devices: List[ShellyDevice] = []
        self.action_results: List[Dict] = []
        self.lock = threading.Lock()
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
        # Default headers
        self.session.headers.update({
            'User-Agent': 'ShellyScanner/1.0',
            'Content-Type': 'application/json'
        })
        
        # Initialize components
        self.rpc_client = ShellyRPCClient(self.session, timeout)
        self.device_manager = DeviceManager(self.rpc_client, self.logger)
        self.network_utils = NetworkUtils()
        
        # Initialize exporter - will be set externally if needed
        self._exporter = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
    
    def execute_action_range(self, start_ip: str, end_octet: int, action_name: str,
                           auth: Optional[Tuple[str, str]] = None,
                           progress_callback=None, **action_kwargs) -> List[Tuple[ShellyDevice, Dict]]:
        """Execute an action on an IP range."""
        if action_name not in AVAILABLE_ACTIONS:
            raise ValueError(f"Unknown action: {action_name}. Available: {list(AVAILABLE_ACTIONS.keys())}")
        
        action = AVAILABLE_ACTIONS[action_name]
        ip_list = self.network_utils.generate_ip_range(start_ip, end_octet)
        self.logger.info(f"Executing '{action_name}' on {len(ip_list)} IP addresses from {start_ip} to {ip_list[-1]}")
        
        results = []
        completed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_ip = {
                executor.submit(self.device_manager.execute_action, ip, action, auth, **action_kwargs): ip 
                for ip in ip_list
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                completed += 1
                
                try:
                    device, result = future.result()
                    results.append((device, result))
                    
                    if progress_callback:
                        progress_callback(completed, len(ip_list), device, result)
                    
                except Exception as e:
                    self.logger.error(f"{ip}: Exception in execute_action: {e}")
                    error_device = ShellyDevice(
                        ip=ip, 
                        status=DeviceStatus.ERROR, 
                        error_message=str(e)
                    )
                    error_result = {
                        "success": False,
                        "action": action_name,
                        "error": str(e)
                    }
                    results.append((error_device, error_result))
        
        # Store results
        self.devices = [device for device, _ in results]
        self.action_results = [result for _, result in results]
        
        return results
    
    def execute_action_list(self, ip_list: List[str], action_name: str,
                          auth: Optional[Tuple[str, str]] = None,
                          progress_callback=None, **action_kwargs) -> List[Tuple[ShellyDevice, Dict]]:
        """Execute an action on a predefined list of IP addresses."""
        if action_name not in AVAILABLE_ACTIONS:
            raise ValueError(f"Unknown action: {action_name}. Available: {list(AVAILABLE_ACTIONS.keys())}")
        
        action = AVAILABLE_ACTIONS[action_name]
        self.logger.info(f"Executing '{action_name}' on {len(ip_list)} predefined IP addresses")
        
        results = []
        completed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_ip = {
                executor.submit(self.device_manager.execute_action, ip, action, auth, **action_kwargs): ip 
                for ip in ip_list
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_ip):
                ip = future_to_ip[future]
                completed += 1
                
                try:
                    device, result = future.result()
                    results.append((device, result))
                    
                    if progress_callback:
                        progress_callback(completed, len(ip_list), device, result)
                    
                except Exception as e:
                    self.logger.error(f"{ip}: Exception in execute_action: {e}")
                    error_device = ShellyDevice(
                        ip=ip, 
                        status=DeviceStatus.ERROR, 
                        error_message=str(e)
                    )
                    error_result = {
                        "success": False,
                        "action": action_name,
                        "error": str(e)
                    }
                    results.append((error_device, error_result))
        
        # Store results
        self.devices = [device for device, _ in results]
        self.action_results = [result for _, result in results]
        
        return results
    
    def scan_range(self, start_ip: str, end_octet: int, 
                   auth: Optional[Tuple[str, str]] = None,
                   progress_callback=None) -> List[ShellyDevice]:
        """Scan IP range for Shelly devices (compatibility method using list action)."""
        results = self.execute_action_range(start_ip, end_octet, "list", auth, progress_callback)
        return [device for device, _ in results]
    
    # Backward compatibility methods
    def get_device_config(self, ip: str, auth: Optional[Tuple[str, str]] = None) -> Dict:
        """Get complete device configuration (compatibility method)."""
        device, result = self.device_manager.execute_action(ip, AVAILABLE_ACTIONS["config-get"], auth)
        return result.get("config", {}) if result["success"] else {}
    
    def set_device_config(self, ip: str, config: Dict, 
                         auth: Optional[Tuple[str, str]] = None) -> bool:
        """Set device configuration (compatibility method)."""
        device, result = self.device_manager.execute_action(
            ip, AVAILABLE_ACTIONS["config-set"], auth, config=config
        )
        return result["success"]
    
    def reboot_device(self, ip: str, auth: Optional[Tuple[str, str]] = None) -> bool:
        """Reboot device (compatibility method)."""
        device, result = self.device_manager.execute_action(ip, AVAILABLE_ACTIONS["reboot"], auth)
        return result["success"]
