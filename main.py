#!/usr/bin/env python3
"""
NetSuite GUI - Main Entry Point
Windows Network Administration Toolkit

This is the main entry point for the application.
Run this file to start NetSuite GUI.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check Python version
if sys.version_info < (3, 8):
    print("Error: NetSuite requires Python 3.8 or higher.")
    print(f"Current version: {sys.version}")
    sys.exit(1)

# Import and run the GUI
try:
    from netsuite_gui import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("\nPlease ensure you're running from the netsuite-windows directory.")
    print("Or install all requirements: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting NetSuite GUI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
