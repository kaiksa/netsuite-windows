"""
Network Information Tool for NetSuite GUI
Displays network interface and configuration information.
"""

import socket
import subprocess
import platform
from tkinter import ttk
from .base_tool import BaseTool


class NetworkInfoTool(BaseTool):
    """Display network interface information and configuration."""
    
    def create_ui(self, parent):
        """Create the network info UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Network Information")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Refresh button
        ttk.Button(input_frame, text="Refresh", command=self.run_tool).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Export button
        ttk.Button(input_frame, text="Export", command=self.export_results).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
        
        # Auto-load on startup
        self.run_tool()
    
    def run_tool(self):
        """Display network information."""
        self.clear_output()
        self.print_header("Network Information")
        
        self.run_in_thread(self._get_network_info)
    
    def _get_network_info(self):
        """Gather and display network information."""
        try:
            self.gui.start_progress()
            self.gui.set_status("Gathering network information...")
            
            # System info
            self.append_output("\n--- System Information ---", 'INFO')
            self.append_output(f"Hostname: {socket.gethostname()}")
            self.append_output(f"Platform: {platform.system()} {platform.release()}")
            
            # IP configuration
            self.append_output("\n--- IP Configuration ---", 'INFO')
            self._get_ipconfig()
            
            # Network interfaces
            self.append_output("\n--- Network Interfaces ---", 'INFO')
            self._get_interfaces()
            
            # Routing table
            self.append_output("\n--- Routing Table ---", 'INFO')
            self._get_route()
            
            # ARP table
            self.append_output("\n--- ARP Table ---", 'INFO')
            self._get_arp()
            
            # Active connections
            self.append_output("\n--- Active Connections ---", 'INFO')
            self._get_connections()
            
            self.append_output("\n" + "=" * 60, 'INFO')
            self.append_output("Network information gathered successfully!", 'SUCCESS')
            
        except Exception as e:
            self.append_output(f"Error gathering network info: {e}", 'ERROR')
        finally:
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _get_ipconfig(self):
        """Get IP configuration using ipconfig."""
        try:
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout
            
            # Parse and format
            current_adapter = None
            for line in output.split('\n'):
                line = line.strip()
                
                if line.startswith('Ethernet') or line.startswith('Wireless') or line.startswith('Wi-Fi'):
                    current_adapter = line
                    self.append_output(f"\n{line}", 'INFO')
                elif current_adapter:
                    if line and not line.startswith('   '):
                        self.append_output(f"  {line}")
        
        except Exception as e:
            self.append_output(f"  Error: {e}", 'ERROR')
    
    def _get_interfaces(self):
        """Get network interface information."""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            self.append_output(f"  Local IP: {local_ip}")
            
            # Get all interfaces
            result = subprocess.run(
                ['ipconfig'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if 'IPv4' in line or 'IPv6' in line:
                    self.append_output(f"  {line.strip()}")
        
        except Exception as e:
            self.append_output(f"  Error: {e}", 'ERROR')
    
    def _get_route(self):
        """Get routing table."""
        try:
            result = subprocess.run(
                ['route', 'print'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Show first few lines of route table
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines[:30]):  # First 30 lines
                if line.strip():
                    self.append_output(f"  {line.rstrip()}")
            
            if len(lines) > 30:
                self.append_output(f"  ... ({len(lines) - 30} more lines)", 'INFO')
        
        except Exception as e:
            self.append_output(f"  Error: {e}", 'ERROR')
    
    def _get_arp(self):
        """Get ARP table."""
        try:
            result = subprocess.run(
                ['arp', '-a'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    self.append_output(f"  {line.rstrip()}")
        
        except Exception as e:
            self.append_output(f"  Error: {e}", 'ERROR')
    
    def _get_connections(self):
        """Get active network connections."""
        try:
            # Get TCP connections (limited)
            result = subprocess.run(
                ['netstat', '-an', '-p', 'tcp'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Show ESTABLISHED connections
            lines = result.stdout.split('\n')
            count = 0
            for line in lines:
                if 'ESTABLISHED' in line:
                    self.append_output(f"  {line.strip()}")
                    count += 1
                    if count >= 20:  # Limit to 20 connections
                        self.append_output(f"  ... (more connections)", 'INFO')
                        break
        
        except Exception as e:
            self.append_output(f"  Error: {e}", 'ERROR')
