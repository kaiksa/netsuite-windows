"""
Configuration Manager for NetSuite GUI
Handles loading and saving configuration settings.
"""

import json
import os
from pathlib import Path


class ConfigManager:
    """Manages application configuration."""
    
    DEFAULT_CONFIG = {
        'general': {
            'theme': 'default',
            'check_updates': True,
            'log_level': 'INFO'
        },
        'ping': {
            'count': 4,
            'timeout': 2,
            'continuous': False
        },
        'port_scanner': {
            'timeout': 1,
            'common_ports_only': True
        },
        'traceroute': {
            'max_hops': 30,
            'timeout': 2
        },
        'network_discovery': {
            'timeout': 1,
            'scan_range': 'auto'
        }
    }
    
    def __init__(self):
        self.app_data_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'NetSuite'
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.app_data_dir / 'config.ini'
        self.config = self.DEFAULT_CONFIG.copy()
        
        self.load()
    
    def load(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    
                # Merge with defaults to handle new keys
                for section, values in saved_config.items():
                    if section in self.config:
                        self.config[section].update(values)
                    else:
                        self.config[section] = values
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, section, key, default=None):
        """Get a configuration value."""
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def set(self, section, key, value):
        """Set a configuration value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def get_section(self, section):
        """Get all values in a section."""
        return self.config.get(section, {})
