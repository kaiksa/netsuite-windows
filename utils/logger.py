"""
Logger for NetSuite GUI
Handles logging to file and console.
"""

import logging
import os
from pathlib import Path
from datetime import datetime


class Logger:
    """Application logger."""
    
    def __init__(self, name='NetSuite'):
        self.name = name
        
        # Create logs directory
        self.app_data_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'NetSuite'
        self.logs_dir = self.app_data_dir / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.log_file = self.logs_dir / f'{name.lower()}.log'
        
        # Configure logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        try:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Format
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error setting up file logger: {e}")
    
    def debug(self, message):
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message):
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message):
        """Log critical message."""
        self.logger.critical(message)
    
    def success(self, message):
        """Log success message."""
        self.logger.info(f"✓ {message}")
    
    def get_logs(self, lines=100):
        """Get last N lines from log file."""
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except Exception:
            return []
