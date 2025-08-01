"""
Network utilities for Shelly device communication.
"""

import ipaddress
import time
import requests
from typing import Dict, List, Optional, Tuple, Any


class NetworkUtils:
    """Utility class for network operations."""
    
    @staticmethod
    def generate_ip_range(start_ip: str, end_octet: int) -> List[str]:
        """Generate list of IP addresses to scan."""
        try:
            start = ipaddress.IPv4Address(start_ip)
            ip_parts = str(start).split('.')
            
            if not (1 <= end_octet <= 254):
                raise ValueError("End octet must be between 1 and 254")
            
            start_octet = int(ip_parts[3])
            if start_octet > end_octet:
                raise ValueError("Start octet cannot be greater than end octet")
            
            ip_base = '.'.join(ip_parts[:3]) + '.'
            return [f"{ip_base}{i}" for i in range(start_octet, end_octet + 1)]
            
        except ipaddress.AddressValueError as e:
            raise ValueError(f"Invalid IP address: {start_ip}") from e


class ShellyRPCClient:
    """RPC client for communicating with Shelly devices."""
    
    def __init__(self, session: requests.Session, timeout: int = 3):
        self.session = session
        self.timeout = timeout
    
    def make_rpc_request(self, ip: str, method: str, params: Optional[Dict] = None,
                        auth: Optional[Tuple[str, str]] = None) -> Tuple[Dict[str, Any], float]:
        """Make RPC request to Shelly Gen4 device."""
        url = f"http://{ip}/rpc/{method}"
        
        payload = {
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        start_time = time.time()
        response = self.session.post(
            url, 
            json=payload, 
            timeout=self.timeout,
            auth=auth
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                raise requests.RequestException(f"RPC Error: {data['error']}")
            return data, response_time
        else:
            response.raise_for_status()
