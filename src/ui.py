"""
User interface utilities for displaying scan results and progress.
"""

from typing import List, Dict, Any
from .models import DeviceStatus, ShellyDevice


class DisplayUtils:
    """Utilities for displaying scan results and progress."""
    
    @staticmethod
    def progress_callback(completed: int, total: int, device: ShellyDevice):
        """Progress callback for scan operation (backward compatibility)."""
        percentage = (completed / total) * 100
        status_icon = {
            DeviceStatus.DETECTED: "✓",
            DeviceStatus.UPDATED: "↑",
            DeviceStatus.NO_UPDATE_NEEDED: "•",
            DeviceStatus.AUTH_REQUIRED: "🔒",
            DeviceStatus.NOT_SHELLY: "✗",
            DeviceStatus.UNREACHABLE: "-",
            DeviceStatus.ERROR: "!"
        }.get(device.status, "?")
        
        print(f"[{percentage:5.1f}%] {device.ip:15} {status_icon} {device.status.value}")
    
    @staticmethod
    def action_progress_callback(completed: int, total: int, device: ShellyDevice, result: Dict[str, Any]):
        """Progress callback for action-based operations."""
        percentage = (completed / total) * 100
        
        # Determine status icon based on action result and device status
        if result["success"]:
            if device.status == DeviceStatus.UPDATED:
                status_icon = "↑"
            elif device.status == DeviceStatus.DETECTED:
                status_icon = "✓"
            elif device.status == DeviceStatus.NO_UPDATE_NEEDED:
                status_icon = "•"
            else:
                status_icon = "✓"
        else:
            if device.status == DeviceStatus.AUTH_REQUIRED:
                status_icon = "🔒"
            elif device.status == DeviceStatus.NOT_SHELLY:
                status_icon = "✗"
            elif device.status == DeviceStatus.UNREACHABLE:
                status_icon = "-"
            else:
                status_icon = "!"
        
        action_name = result.get("action", "unknown")
        status_text = "success" if result["success"] else result.get("error", "failed")
        
        print(f"[{percentage:5.1f}%] {device.ip:15} {status_icon} {action_name}: {status_text}")
    
    @staticmethod
    def print_summary(devices: List[ShellyDevice]):
        """Print scan summary (backward compatibility)."""
        DisplayUtils.print_action_summary(devices, [], "list")
    
    @staticmethod
    def print_action_summary(devices: List[ShellyDevice], action_results: List[Dict], action_name: str):
        """Print summary for action-based operations."""
        if not devices:
            print("No results available.")
            return
        
        # Count devices by status
        status_counts = {}
        success_count = 0
        error_count = 0
        auth_required_devices = []
        successful_devices = []
        
        for i, device in enumerate(devices):
            status_counts[device.status] = status_counts.get(device.status, 0) + 1
            
            if i < len(action_results):
                result = action_results[i]
                if result["success"]:
                    success_count += 1
                    if device.status in [DeviceStatus.DETECTED, DeviceStatus.UPDATED, DeviceStatus.NO_UPDATE_NEEDED]:
                        successful_devices.append((device, result))
                else:
                    # Only count as error if it's not a NOT_SHELLY device
                    if device.status != DeviceStatus.NOT_SHELLY:
                        error_count += 1
            
            if device.status == DeviceStatus.AUTH_REQUIRED:
                auth_required_devices.append(device)
        
        print("\n" + "="*70)
        print(f"ACTION SUMMARY: {action_name.upper()}")
        print("="*70)
        
        print(f"Total IPs processed: {len(devices)}")
        print(f"Successful operations: {success_count}")
        print(f"Failed operations: {error_count}")
        print(f"Shelly devices found: {len([d for d in devices if d.status in [DeviceStatus.DETECTED, DeviceStatus.UPDATED, DeviceStatus.NO_UPDATE_NEEDED]])}")
        
        # Action-specific summary
        if action_name == "update":
            print(f"Updates started: {status_counts.get(DeviceStatus.UPDATED, 0)}")
            print(f"No update needed: {status_counts.get(DeviceStatus.NO_UPDATE_NEEDED, 0)}")
        elif action_name == "status":
            # Count devices with available updates
            devices_with_updates = 0
            for i, result in enumerate(action_results):
                if result.get("success") and result.get("update_info", {}).get("available"):
                    devices_with_updates += 1
            print(f"Devices with updates available: {devices_with_updates}")
        
        print(f"Auth required: {len(auth_required_devices)}")
        print(f"Not Shelly devices: {status_counts.get(DeviceStatus.NOT_SHELLY, 0)}")
        print(f"Unreachable: {status_counts.get(DeviceStatus.UNREACHABLE, 0)}")
        print(f"Errors: {status_counts.get(DeviceStatus.ERROR, 0)}")
        
        if successful_devices:
            print(f"\nSUCCESSFUL {action_name.upper()} OPERATIONS:")
            print("-" * 70)
            for device, result in successful_devices:
                status_icon = "✓" if device.status == DeviceStatus.UPDATED else "•"
                response_time = f" ({device.response_time:.2f}s)" if device.response_time else ""
                message = result.get("message", "Success")
                
                # For status action, show update availability prominently
                if action_name == "status":
                    update_info = result.get("update_info", {})
                    if update_info.get("available"):
                        status_icon = "🔄"  # Update available icon
                        # Show available update versions
                        stable = update_info.get("stable_update", {})
                        beta = update_info.get("beta_update", {})
                        update_parts = []
                        if stable and stable.get("available"):
                            update_parts.append(f"Stable: {stable.get('version')}")
                        if beta and beta.get("available"):
                            update_parts.append(f"Beta: {beta.get('version')}")
                        if update_parts:
                            message += f" | Updates: {', '.join(update_parts)}"
                
                print(f"{status_icon} {device.ip:15} | {device.device_type or 'Unknown':15} | "
                      f"{device.firmware_version or 'Unknown':15} | {message}{response_time}")
        
        if auth_required_devices:
            print(f"\nDEVICES REQUIRING AUTHENTICATION:")
            print("-" * 40)
            for device in auth_required_devices:
                print(f"• {device.ip}")
            print("\nUse --username and --password options for authenticated devices.")
        
        # Show action-specific results
        if action_name == "status":
            print(f"\nFor detailed status and update information, use --export json")
            # Show summary of devices with updates
            devices_with_updates = []
            for i, result in enumerate(action_results):
                if (result.get("success") and 
                    result.get("update_info", {}).get("available") and 
                    i < len(devices)):
                    devices_with_updates.append((devices[i], result))
            
            if devices_with_updates:
                print(f"\nDEVICES WITH AVAILABLE UPDATES:")
                print("-" * 50)
                for device, result in devices_with_updates:
                    update_info = result["update_info"]
                    stable = update_info.get("stable_update", {})
                    beta = update_info.get("beta_update", {})
                    
                    update_line = f"🔄 {device.ip:15} | Current: {device.firmware_version or 'Unknown'}"
                    if stable and stable.get("available"):
                        update_line += f" | Stable: {stable.get('version')}"
                    if beta and beta.get("available"):
                        update_line += f" | Beta: {beta.get('version')}"
                    print(update_line)
                
                print(f"\nTo update these devices, run:")
                print(f"  python -m src.main --start <start_ip> --end <end_ip> --action update")
        
        elif action_name in ["config-get"]:
            print(f"\nFor detailed {action_name} data, check the exported file (--export json)")
        
        # Show errors
        error_devices = [(devices[i], action_results[i]) for i in range(min(len(devices), len(action_results))) 
                        if not action_results[i]["success"] and devices[i].status not in [DeviceStatus.AUTH_REQUIRED, DeviceStatus.NOT_SHELLY, DeviceStatus.UNREACHABLE]]
        
        if error_devices:
            print(f"\nERRORS:")
            print("-" * 40)
            for device, result in error_devices[:10]:  # Show first 10 errors
                error_msg = result.get("error", "Unknown error")
                print(f"! {device.ip:15} | {error_msg}")
            
            if len(error_devices) > 10:
                print(f"... and {len(error_devices) - 10} more errors")
