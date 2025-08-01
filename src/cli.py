"""
Command-line interface for Shelly device scanner with action support.
"""

import argparse
import sys
import json
from typing import Optional, Tuple

from .scanner import ShellyScanner
from .exporter import ResultsExporter
from .ui import DisplayUtils
from .actions import AVAILABLE_ACTIONS
from .config import get_config_manager, ConfigManager


class CLI:
    """Command-line interface handler with action support."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser."""
        parser = argparse.ArgumentParser(
            description="Production Shelly Gen4 device scanner and management tool.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"""
Available Actions:
{self._format_actions()}

Examples:
  # List/discover devices using IP range
  %(prog)s --start 192.168.1.100 --end 150 --action list

  # List devices using predefined IPs from config file
  %(prog)s --config shelly_config.json --action list

  # Update firmware on devices from config (stable channel)
  %(prog)s --config shelly_config.json --action update --verbose

  # Update firmware to beta channel
  %(prog)s --start 192.168.1.1 --end 10 --action update --update-channel beta

  # Reboot specific devices using range
  %(prog)s --start 192.168.1.100 --end 105 --action reboot --username admin --password secret

  # Get device status from predefined IPs
  %(prog)s --config shelly_config.json --action status --export json

  # Create a sample configuration file
  %(prog)s --create-config

  # Get device configurations using config file
  %(prog)s --config shelly_config.json --action config-get --export json
            """
        )
        
        # IP source arguments (mutually exclusive)
        ip_group = parser.add_mutually_exclusive_group(required=False)
        ip_group.add_argument('--start', 
                             help='Start IP address for range scan (e.g., 192.168.1.100)')
        ip_group.add_argument('--config', 
                             help='Configuration file with predefined IP addresses')
        
        # Range scan arguments (only used with --start)
        parser.add_argument('--end', type=int,
                           help='End IP last octet (e.g., 150) - required when using --start')
        
        # Required action (unless creating config)
        parser.add_argument('--action', 
                           choices=list(AVAILABLE_ACTIONS.keys()),
                           help='Action to perform on discovered devices')
        
        # Configuration management
        parser.add_argument('--create-config', action='store_true',
                           help='Create a sample configuration file and exit')
        parser.add_argument('--config-output', 
                           help='Output filename for --create-config (default: shelly_config.json)')
        
        # Optional arguments
        parser.add_argument('--username', help='Username for authenticated devices')
        parser.add_argument('--password', help='Password for authenticated devices')
        parser.add_argument('--timeout', type=int, default=3,
                           help='Request timeout in seconds (default: 3)')
        parser.add_argument('--max-workers', type=int, default=50,
                           help='Maximum concurrent threads (default: 50)')
        parser.add_argument('--export', choices=['json', 'csv'],
                           help='Export results to file (json or csv)')
        parser.add_argument('--export-file', help='Custom export filename')
        parser.add_argument('--verbose', '-v', action='store_true',
                           help='Enable verbose output')
        parser.add_argument('--verify-ssl', action='store_true',
                           help='Verify SSL certificates (default: disabled)')
        parser.add_argument('--no-progress', action='store_true',
                           help='Disable progress output')
        
        # Action-specific arguments
        parser.add_argument('--config-file', help='JSON file containing configuration for config-set action')
        parser.add_argument('--config-data', help='JSON string containing configuration for config-set action')
        parser.add_argument('--update-channel', choices=['stable', 'beta'], default='stable',
                           help='Update channel for firmware updates (default: stable)')
        
        return parser
    
    def _format_actions(self) -> str:
        """Format available actions for help text."""
        lines = []
        for name, action in AVAILABLE_ACTIONS.items():
            lines.append(f"  {name:<12} - {action.description}")
        return "\n".join(lines)
    
    def parse_args(self, args=None):
        """Parse command line arguments."""
        return self.parser.parse_args(args)
    
    def validate_args(self, args) -> bool:
        """Validate parsed arguments."""
        # Handle config file creation
        if args.create_config:
            return True  # Skip other validations for config creation
        
        # Action is required unless creating config
        if not args.action:
            print("Error: --action is required")
            return False
        
        # IP source is required unless creating config
        if not args.start and not args.config:
            print("Error: Either --start or --config is required")
            return False
        
        # Validate that we have either start+end or config
        if args.start and not args.end:
            print("Error: --end is required when using --start")
            return False
        
        if args.start and args.end:
            if args.end < 1 or args.end > 254:
                print("Error: End octet must be between 1 and 254")
                return False
        
        if args.max_workers < 1 or args.max_workers > 200:
            print("Error: max-workers must be between 1 and 200")
            return False
        
        if (args.username and not args.password) or (args.password and not args.username):
            print("Error: Both --username and --password must be provided")
            return False
        
        # Validate action-specific arguments
        if args.action == "config-set":
            if not args.config_file and not args.config_data:
                print("Error: config-set action requires --config-file or --config-data")
                return False
            
            if args.config_file and args.config_data:
                print("Error: Specify either --config-file or --config-data, not both")
                return False
        
        return True
    
    def setup_auth(self, args) -> Optional[Tuple[str, str]]:
        """Setup authentication from arguments."""
        if args.username and args.password:
            return (args.username, args.password)
        return None
    
    def prepare_action_kwargs(self, args) -> dict:
        """Prepare action-specific keyword arguments."""
        kwargs = {}
        
        if args.action == "config-set":
            if args.config_file:
                try:
                    with open(args.config_file, 'r') as f:
                        kwargs['config'] = json.load(f)
                except Exception as e:
                    raise ValueError(f"Failed to load config file: {e}")
            
            elif args.config_data:
                try:
                    kwargs['config'] = json.loads(args.config_data)
                except Exception as e:
                    raise ValueError(f"Failed to parse config data: {e}")
        
        elif args.action == "update":
            # Add update channel parameter
            kwargs['channel'] = args.update_channel
        
        return kwargs
    
    def run(self, args=None):
        """Run the CLI application."""
        args = self.parse_args(args)
        
        # Handle config file creation
        if args.create_config:
            try:
                config_manager = ConfigManager()
                filename = config_manager.create_sample_config(args.config_output)
                print(f"Sample configuration file created: {filename}")
                print("\nEdit this file to add your Shelly device IP addresses.")
                return
            except Exception as e:
                print(f"Error creating config file: {e}")
                sys.exit(1)
        
        if not self.validate_args(args):
            sys.exit(1)
        
        # Load configuration if specified
        config_manager = None
        predefined_ips = []
        
        if args.config:
            config_manager = get_config_manager(args.config)
            predefined_ips = config_manager.get_predefined_ips()
            
            if not predefined_ips:
                print(f"Warning: No predefined IPs found in config file {args.config}")
                print("Make sure the config file contains a 'predefined_ips' array.")
                sys.exit(1)
            
            # Use default credentials from config if not provided via CLI
            if not args.username and not args.password:
                default_creds = config_manager.get_default_credentials()
                if default_creds:
                    args.username = default_creds.get('username')
                    args.password = default_creds.get('password')
            
            # Apply scan settings from config
            scan_settings = config_manager.get_scan_settings()
            if not hasattr(args, 'timeout') or args.timeout == 3:  # Default timeout
                args.timeout = scan_settings.get('timeout', args.timeout)
            if not hasattr(args, 'max_workers') or args.max_workers == 50:  # Default workers
                args.max_workers = scan_settings.get('max_workers', args.max_workers)
            if not hasattr(args, 'verify_ssl') or not args.verify_ssl:
                args.verify_ssl = scan_settings.get('verify_ssl', args.verify_ssl)
            
            # Apply update settings from config if not specified via CLI
            update_settings = config_manager.get_update_settings()
            if args.update_channel == 'stable':  # Default value, might be overridden by config
                args.update_channel = update_settings.get('default_channel', args.update_channel)
        
        auth = self.setup_auth(args)
        
        try:
            action_kwargs = self.prepare_action_kwargs(args)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        
        try:
            with ShellyScanner(
                timeout=args.timeout,
                max_workers=args.max_workers,
                verbose=args.verbose,
                verify_ssl=args.verify_ssl
            ) as scanner:
                
                # Create exporter
                exporter = ResultsExporter(scanner.logger)
                
                # Execute action based on IP source
                def progress_callback(completed, total, device, result):
                    if not args.no_progress:
                        DisplayUtils.action_progress_callback(completed, total, device, result)
                
                callback = progress_callback if not args.no_progress else None
                
                if predefined_ips:
                    # Use predefined IPs from config file
                    print(f"Using {len(predefined_ips)} predefined IP addresses from config")
                    results = scanner.execute_action_list(
                        predefined_ips, args.action, auth, callback, **action_kwargs
                    )
                else:
                    # Use IP range scan
                    results = scanner.execute_action_range(
                        args.start, args.end, args.action, auth, callback, **action_kwargs
                    )
                
                # Extract devices and action results
                devices = [device for device, _ in results]
                action_results = [result for _, result in results]
                
                # Print summary
                DisplayUtils.print_action_summary(devices, action_results, args.action)
                
                # Export results if requested
                if args.export:
                    # Create enhanced export data including action results
                    export_data = []
                    for device, result in results:
                        device_data = device.to_dict()
                        device_data['action_result'] = result
                        export_data.append(device_data)
                    
                    # Use a custom export for action results
                    filename = self._export_action_results(
                        export_data, args.export, args.export_file, 
                        args.action, exporter
                    )
                    print(f"\nResults exported to: {filename}")
        
        except KeyboardInterrupt:
            print("\nOperation interrupted by user.")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)
    
    def _export_action_results(self, export_data, format_type, filename, action, exporter):
        """Export action results with custom filename."""
        if not filename:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"shelly_{action}_{timestamp}.{format_type}"
        
        # Create a temporary device list for compatibility with exporter
        temp_devices = []
        for data in export_data:
            from .models import ShellyDevice, DeviceStatus
            device = ShellyDevice(
                ip=data['ip'],
                status=DeviceStatus(data['status']),
                device_id=data.get('device_id'),
                device_type=data.get('device_type'),
                firmware_version=data.get('firmware_version'),
                device_name=data.get('device_name'),
                auth_required=data.get('auth_required', False),
                last_seen=data.get('last_seen'),
                response_time=data.get('response_time'),
                error_message=data.get('error_message')
            )
            temp_devices.append(device)
        
        return exporter.export_results(temp_devices, format_type, filename)
