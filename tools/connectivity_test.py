"""
Connectivity Test Tool for NetSuite GUI
Tests internet connectivity and connection quality.
"""

import socket
import subprocess
import time
import tkinter as tk
from tkinter import ttk
from .base_tool import BaseTool


class ConnectivityTestTool(BaseTool):
    """Internet connectivity testing tool."""
    
    # Test endpoints
    TEST_HOSTS = [
        ('DNS', '8.8.8.8', 53),
        ('Google DNS', '8.8.4.4', 53),
        ('Cloudflare', '1.1.1.1', 53),
        ('Google', 'www.google.com', 80),
        ('Cloudflare HTTPS', 'www.cloudflare.com', 443)
    ]
    
    def create_ui(self, parent):
        """Create the connectivity test UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Connectivity Test")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Custom host input
        ttk.Label(input_frame, text="Custom Host (optional):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.host_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.host_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        
        # Test type
        ttk.Label(input_frame, text="Test:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.test_type_var = tk.StringVar(value="full")
        ttk.Combobox(input_frame, textvariable=self.test_type_var, 
                    values=["full", "quick", "custom"], width=10, 
                    state="readonly").grid(row=0, column=3, padx=5, pady=5)
        
        # Test button
        ttk.Button(input_frame, text="Test", command=self.run_tool).grid(row=0, column=4, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Run connectivity test."""
        self.clear_output()
        self.print_header("Internet Connectivity Test")
        
        self.run_in_thread(self._test_connectivity)
    
    def _test_connectivity(self):
        """Perform connectivity tests."""
        try:
            self.gui.start_progress()
            self.gui.set_status("Testing connectivity...")
            
            # Test 1: DNS Resolution
            self.append_output("\n--- DNS Resolution Test ---", 'INFO')
            self._test_dns()
            
            # Test 2: TCP Connection Tests
            self.append_output("\n--- TCP Connection Tests ---", 'INFO')
            self._test_tcp_connections()
            
            # Test 3: ICMP Ping Tests
            self.append_output("\n--- ICMP Ping Tests ---", 'INFO')
            self._test_ping()
            
            # Test 4: Gateway connectivity
            self.append_output("\n--- Gateway Connectivity ---", 'INFO')
            self._test_gateway()
            
            # Test 5: Custom host if specified
            custom_host = self.host_var.get().strip()
            if custom_host:
                self.append_output("\n--- Custom Host Test ---", 'INFO')
                self._test_custom_host(custom_host)
            
            # Summary
            self.append_output("\n" + "=" * 60, 'INFO')
            self.append_output("Connectivity test complete!", 'SUCCESS')
            self.append_output("=" * 60, 'INFO')
        
        except Exception as e:
            self.append_output(f"Error during test: {e}", 'ERROR')
        finally:
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _test_dns(self):
        """Test DNS resolution."""
        test_domains = ['www.google.com', 'www.cloudflare.com', 'github.com']
        
        for domain in test_domains:
            try:
                ip = socket.gethostbyname(domain)
                self.append_output(f"  ✓ {domain} -> {ip}", 'SUCCESS')
            except socket.gaierror:
                self.append_output(f"  ✗ {domain} - Failed to resolve", 'ERROR')
    
    def _test_tcp_connections(self):
        """Test TCP connections to various endpoints."""
        test_type = self.test_type_var.get()
        
        hosts = self.TEST_HOSTS if test_type in ['full', 'quick'] else []
        
        for name, host, port in hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                
                start = time.time()
                result = sock.connect_ex((host, port))
                elapsed = (time.time() - start) * 1000
                
                sock.close()
                
                if result == 0:
                    self.append_output(f"  ✓ {name} ({host}:{port}) - {elapsed:.0f}ms", 'SUCCESS')
                else:
                    self.append_output(f"  ✗ {name} ({host}:{port}) - Failed", 'ERROR')
            
            except Exception as e:
                self.append_output(f"  ✗ {name} ({host}:{port}) - {e}", 'ERROR')
    
    def _test_ping(self):
        """Test ICMP ping connectivity."""
        test_hosts = ['8.8.8.8', '1.1.1.1']
        
        for host in test_hosts:
            try:
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', '2000', host],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if 'Reply from' in result.stdout:
                    # Extract time
                    import re
                    match = re.search(r'time[=<](\d+)ms', result.stdout)
                    if match:
                        self.append_output(f"  ✓ {host} - {match.group(1)}ms", 'SUCCESS')
                    else:
                        self.append_output(f"  ✓ {host} - Reachable", 'SUCCESS')
                else:
                    self.append_output(f"  ✗ {host} - Unreachable", 'ERROR')
            
            except Exception as e:
                self.append_output(f"  ✗ {host} - Error: {e}", 'ERROR')
    
    def _test_gateway(self):
        """Test default gateway connectivity."""
        try:
            # Get default gateway from route table
            result = subprocess.run(
                ['route', 'print', '0.0.0.0'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse gateway
            for line in result.stdout.split('\n'):
                if '0.0.0.0' in line and line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        gateway = parts[2]
                        if self._is_valid_ip(gateway):
                            # Test gateway
                            ping_result = subprocess.run(
                                ['ping', '-n', '1', '-w', '1000', gateway],
                                capture_output=True,
                                text=True,
                                timeout=3
                            )
                            
                            if 'Reply from' in ping_result.stdout:
                                self.append_output(f"  ✓ Gateway {gateway} - Reachable", 'SUCCESS')
                            else:
                                self.append_output(f"  ✗ Gateway {gateway} - Unreachable", 'ERROR')
                            return
        
            self.append_output("  Unable to determine default gateway", 'WARNING')
        
        except Exception as e:
            self.append_output(f"  Error: {e}", 'ERROR')
    
    def _test_custom_host(self, host):
        """Test connectivity to custom host."""
        # Try to resolve
        try:
            ip = socket.gethostbyname(host)
            self.append_output(f"  Resolved: {host} -> {ip}", 'INFO')
        except socket.gaierror:
            self.append_output(f"  Failed to resolve: {host}", 'ERROR')
            return
        
        # Try to ping
        try:
            result = subprocess.run(
                ['ping', '-n', '2', '-w', '3000', host],
                capture_output=True,
                text=True,
                timeout=8
            )
            
            if 'Reply from' in result.stdout:
                import re
                times = re.findall(r'time[=<](\d+)ms', result.stdout)
                if times:
                    avg = sum(int(t) for t in times) / len(times)
                    self.append_output(f"  ✓ Ping: {host} - Average {avg:.0f}ms", 'SUCCESS')
                else:
                    self.append_output(f"  ✓ Ping: {host} - Reachable", 'SUCCESS')
            else:
                self.append_output(f"  ✗ Ping: {host} - Failed", 'ERROR')
        
        except Exception as e:
            self.append_output(f"  ✗ Error: {e}", 'ERROR')
    
    def _is_valid_ip(self, s):
        """Check if string is a valid IP address."""
        try:
            parts = s.split('.')
            return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
        except:
            return False
