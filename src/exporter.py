"""
Export functionality for Shelly scan results.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import ShellyDevice


class ResultsExporter:
    """Handles exporting scan results to various formats."""
    
    def __init__(self, logger):
        self.logger = logger
    
    def export_results(self, devices: List[ShellyDevice], format_type: str = 'json', 
                      filename: Optional[str] = None) -> str:
        """Export scan results to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"shelly_scan_{timestamp}.{format_type}"
        
        filepath = Path(filename)
        
        if format_type.lower() == 'json':
            self._export_json(devices, filepath)
        elif format_type.lower() == 'csv':
            self._export_csv(devices, filepath)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        self.logger.info(f"Results exported to {filepath}")
        return str(filepath)
    
    def _export_json(self, devices: List[ShellyDevice], filepath: Path):
        """Export devices to JSON format."""
        with open(filepath, 'w') as f:
            json.dump([device.to_dict() for device in devices], f, indent=2)
    
    def _export_csv(self, devices: List[ShellyDevice], filepath: Path):
        """Export devices to CSV format."""
        with open(filepath, 'w', newline='') as f:
            if devices:
                writer = csv.DictWriter(f, fieldnames=devices[0].to_dict().keys())
                writer.writeheader()
                for device in devices:
                    writer.writerow(device.to_dict())
