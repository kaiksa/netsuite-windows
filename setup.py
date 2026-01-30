#!/usr/bin/env python3
"""
Setup script for NetSuite GUI
Builds standalone executable using PyInstaller
"""

import os
import sys
import subprocess

def build_executable():
    """Build standalone executable using PyInstaller."""
    print("=" * 60)
    print("NetSuite GUI - Build Script")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✓ PyInstaller found (version: {PyInstaller.__version__})")
    except ImportError:
        print("✗ PyInstaller not found.")
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
    
    print("\nBuilding executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",              # Create single executable
        "--windowed",             # Hide console window
        "--name=NetSuite",        # Output executable name
        "--icon=NONE",            # No icon (add one if available)
        "--add-data=tools;tools", # Include tools directory
        "--add-data=utils;utils", # Include utils directory
        "--clean",                # Clean cache before building
        "netsuite_gui.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        
        print("\n" + "=" * 60)
        print("Build successful!")
        print("=" * 60)
        print(f"Executable location: dist/NetSuite.exe")
        print("\nYou can now distribute NetSuite.exe to any Windows machine.")
        print("No Python installation required.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n✗ PyInstaller not found in PATH.")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("NetSuite GUI Build Script")
            print("\nUsage:")
            print("  python setup.py              Build executable")
            print("  python setup.py --help       Show this help")
            print("\nThis script creates a standalone Windows executable")
            print("using PyInstaller. The resulting executable can be")
            print("distributed without requiring Python installation.")
            return
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information.")
            sys.exit(1)
    
    build_executable()


if __name__ == "__main__":
    main()
