#!/usr/bin/env python3
"""
NetSuite GUI - Windows Network Administration Toolkit
A graphical interface for network diagnostics and administration tools.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import queue
import socket
import time
import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
import ipaddress

# Import tool modules
from tools.dns_lookup import DNSLookupTool
from tools.ping_tool import PingTool
from tools.port_scanner import PortScannerTool
from tools.traceroute import TracerouteTool
from tools.network_info import NetworkInfoTool
from tools.whois_tool import WHOISTool
from tools.connectivity_test import ConnectivityTestTool
from tools.ip_geolocation import IPGeolocationTool
from tools.subnet_calculator import SubnetCalculatorTool
from tools.network_discovery import NetworkDiscoveryTool
from tools.ssl_checker import SSLCheckerTool
from tools.http_headers import HTTPHeadersTool
from tools.wol_tool import WakeOnLanTool
from tools.bandwidth_monitor import BandwidthMonitorTool

from utils.config_manager import ConfigManager
from utils.logger import Logger


class NetSuiteGUI:
    """Main application window for NetSuite GUI."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("NetSuite - Network Administration Toolkit")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Initialize configuration and logging
        self.config_manager = ConfigManager()
        self.logger = Logger()
        
        # Create app data directory
        self.app_data_dir = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'NetSuite'
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize tools
        self.tools = {}
        self._init_tools()
        
        # Build UI
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        # Load settings
        self._load_settings()
        
        # Log startup
        self.logger.info("NetSuite GUI started")
        
        # Handle close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _init_tools(self):
        """Initialize all tool modules."""
        self.tools = {
            'DNS Lookup': DNSLookupTool(self),
            'Ping': PingTool(self),
            'Port Scanner': PortScannerTool(self),
            'Traceroute': TracerouteTool(self),
            'Network Info': NetworkInfoTool(self),
            'WHOIS': WHOISTool(self),
            'Connectivity Test': ConnectivityTestTool(self),
            'IP Geolocation': IPGeolocationTool(self),
            'Subnet Calculator': SubnetCalculatorTool(self),
            'Network Discovery': NetworkDiscoveryTool(self),
            'SSL Checker': SSLCheckerTool(self),
            'HTTP Headers': HTTPHeadersTool(self),
            'Wake-on-LAN': WakeOnLanTool(self),
            'Bandwidth Monitor': BandwidthMonitorTool(self),
            'Logs': None  # Special tab for logs
        }
    
    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Results...", command=self._export_results)
        file_menu.add_command(label="Save Configuration", command=self._save_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        categories = {
            'DNS & Network': ['DNS Lookup', 'Network Info', 'Connectivity Test'],
            'Scanning': ['Port Scanner', 'Network Discovery', 'Ping'],
            'Routing': ['Traceroute'],
            'Information': ['WHOIS', 'IP Geolocation', 'HTTP Headers', 'SSL Checker'],
            'Calculators': ['Subnet Calculator'],
            'Utilities': ['Wake-on-LAN', 'Bandwidth Monitor']
        }
        
        for category, tool_names in categories.items():
            cat_menu = tk.Menu(tools_menu, tearoff=0)
            tools_menu.add_cascade(label=category, menu=cat_menu)
            for tool_name in tool_names:
                cat_menu.add_command(label=tool_name, 
                                    command=lambda t=tool_name: self._switch_to_tool(t))
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Clear Output", command=self._clear_current_output)
        view_menu.add_command(label="Refresh Network Info", command=self._refresh_network_info)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Documentation", command=self._show_docs)
    
    def _create_main_layout(self):
        """Create the main application layout."""
        # Create main container with sidebar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar for tool selection
        sidebar = ttk.Frame(main_frame, width=200, relief=tk.RIDGE)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Sidebar title
        ttk.Label(sidebar, text="Network Tools", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Tool categories in sidebar
        categories_frame = ttk.Frame(sidebar)
        categories_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create buttons for each tool
        for tool_name in self.tools.keys():
            btn = ttk.Button(categories_frame, text=tool_name,
                           command=lambda t=tool_name: self._switch_to_tool(t))
            btn.pack(fill=tk.X, pady=2, padx=2)
        
        # Content area
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs for each tool
        self.tool_frames = {}
        for tool_name, tool in self.tools.items():
            if tool is not None:  # Skip None tools (like Logs)
                frame = ttk.Frame(self.notebook)
                self.notebook.add(frame, text=tool_name)
                self.tool_frames[tool_name] = frame
                tool.create_ui(frame)
            else:
                # Special handling for Logs tab
                frame = ttk.Frame(self.notebook)
                self.notebook.add(frame, text=tool_name)
                self.tool_frames[tool_name] = frame
                self._create_logs_tab(frame)
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def _create_logs_tab(self, parent):
        """Create the logs viewer tab."""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Refresh", 
                  command=self._refresh_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Clear Logs", 
                  command=self._clear_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Export Logs", 
                  command=self._export_logs).pack(side=tk.LEFT, padx=2)
        
        # Log display
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_display = scrolledtext.ScrolledText(log_frame, 
                                                     wrap=tk.WORD,
                                                     font=('Consolas', 9))
        self.log_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for color coding
        self.log_display.tag_config('INFO', foreground='blue')
        self.log_display.tag_config('WARNING', foreground='orange')
        self.log_display.tag_config('ERROR', foreground='red')
        self.log_display.tag_config('SUCCESS', foreground='green')
        
        # Load initial logs
        self._refresh_logs()
    
    def _create_status_bar(self):
        """Create the status bar at the bottom."""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(self.status_bar, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def _switch_to_tool(self, tool_name):
        """Switch to a specific tool tab."""
        if tool_name in self.tool_frames:
            index = list(self.tool_frames.keys()).index(tool_name)
            self.notebook.select(index)
    
    def _on_tab_changed(self, event):
        """Handle tab change events."""
        current_tab = self.notebook.index(self.notebook.select())
        tab_name = list(self.tool_frames.keys())[current_tab]
        self.set_status(f"Tool: {tab_name}")
    
    def set_status(self, message):
        """Update the status bar message."""
        self.status_label.config(text=message)
    
    def start_progress(self):
        """Start the progress indicator."""
        self.progress.start(10)
    
    def stop_progress(self):
        """Stop the progress indicator."""
        self.progress.stop()
    
    def append_output(self, text, tag=None):
        """Append text to the current tool's output."""
        current_tab = self.notebook.index(self.notebook.select())
        tab_name = list(self.tool_frames.keys())[current_tab]
        
        if tab_name in self.tools and self.tools[tab_name]:
            self.tools[tab_name].append_output(text, tag)
    
    def clear_output(self):
        """Clear the current tool's output."""
        current_tab = self.notebook.index(self.notebook.select())
        tab_name = list(self.tool_frames.keys())[current_tab]
        
        if tab_name in self.tools and self.tools[tab_name]:
            self.tools[tab_name].clear_output()
    
    def _clear_current_output(self):
        """Clear the current output pane."""
        self.clear_output()
    
    def _refresh_network_info(self):
        """Refresh network information."""
        if 'Network Info' in self.tools:
            self.tools['Network Info'].run_tool()
    
    def _refresh_logs(self):
        """Refresh the logs display."""
        if hasattr(self, 'log_display'):
            self.log_display.delete(1.0, tk.END)
            
            log_file = self.app_data_dir / 'logs' / 'netsuite.log'
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    for line in lines[-1000:]:  # Last 1000 lines
                        # Parse log level and color code
                        if 'ERROR' in line:
                            self.log_display.insert(tk.END, line, 'ERROR')
                        elif 'WARNING' in line:
                            self.log_display.insert(tk.END, line, 'WARNING')
                        elif 'INFO' in line:
                            self.log_display.insert(tk.END, line, 'INFO')
                        elif 'SUCCESS' in line:
                            self.log_display.insert(tk.END, line, 'SUCCESS')
                        else:
                            self.log_display.insert(tk.END, line)
                except Exception as e:
                    self.log_display.insert(tk.END, f"Error reading logs: {e}\n", 'ERROR')
            
            self.log_display.see(tk.END)
    
    def _clear_logs(self):
        """Clear the log file."""
        log_file = self.app_data_dir / 'logs' / 'netsuite.log'
        try:
            log_file.write_text('')
            self._refresh_logs()
            messagebox.showinfo("Logs Cleared", "Log file has been cleared.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear logs: {e}")
    
    def _export_logs(self):
        """Export logs to a file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Logs"
        )
        
        if file_path:
            try:
                log_file = self.app_data_dir / 'logs' / 'netsuite.log'
                if log_file.exists():
                    import shutil
                    shutil.copy(log_file, file_path)
                    messagebox.showinfo("Export Complete", f"Logs exported to {file_path}")
                else:
                    messagebox.showwarning("No Logs", "No log file found to export.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export logs: {e}")
    
    def _export_results(self):
        """Export current results to a file."""
        current_tab = self.notebook.index(self.notebook.select())
        tab_name = list(self.tool_frames.keys())[current_tab]
        
        if tab_name in self.tools and self.tools[tab_name]:
            self.tools[tab_name].export_results()
    
    def _save_settings(self):
        """Save current configuration."""
        self.config_manager.save()
        messagebox.showinfo("Settings Saved", "Configuration has been saved.")
    
    def _load_settings(self):
        """Load saved configuration."""
        self.config_manager.load()
    
    def _show_about(self):
        """Show the about dialog."""
        about_text = """NetSuite GUI - Network Administration Toolkit

Version: 1.0.0
A comprehensive network diagnostics and administration toolkit for Windows.

Features:
• DNS Lookup & Network Scanning
• Ping, Traceroute, Port Scanner
• WHOIS & IP Geolocation
• SSL/TLS Certificate Checking
• HTTP Headers Inspection
• Wake-on-LAN & Bandwidth Monitoring
• And much more...

Author: Kai
GitHub: github.com/kaiksa/netsuite-windows"""
        
        messagebox.showinfo("About NetSuite", about_text)
    
    def _show_docs(self):
        """Show documentation."""
        docs_text = """NetSuite GUI Documentation

DNS Lookup:
  Enter a domain name to lookup DNS records.

Ping:
  Enter a host/IP to ping. Use continuous ping for ongoing monitoring.

Port Scanner:
  Enter target IP and port range to scan for open ports.

Traceroute:
  Enter destination to trace the network path.

Network Discovery:
  Scan your local network to discover active devices.

WHOIS:
  Lookup domain registration information.

IP Geolocation:
  Get geographical information for an IP address.

Subnet Calculator:
  Calculate network details from IP/CIDR.

SSL Checker:
  Verify SSL/TLS certificates for HTTPS sites.

HTTP Headers:
  Inspect HTTP response headers.

Wake-on-LAN:
  Send magic packet to wake up a remote device.

Bandwidth Monitor:
  Monitor network interface bandwidth usage.

Keyboard Shortcuts:
  Ctrl+E: Export results
  Ctrl+C: Copy selected text"""
        
        messagebox.showinfo("Documentation", docs_text)
    
    def _on_closing(self):
        """Handle application close event."""
        if messagebox.askokcancel("Quit", "Do you want to exit NetSuite?"):
            self._save_settings()
            self.logger.info("NetSuite GUI closed")
            self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    
    # Set Windows theme if available
    try:
        style = ttk.Style()
        style.theme_use('vista') if 'vista' in style.theme_names() else style.theme_use('clam')
    except:
        pass
    
    app = NetSuiteGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
