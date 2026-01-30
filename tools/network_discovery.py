"""
Network Discovery Tool for NetSuite GUI
Scans local network to discover active devices.
"""

import socket
import subprocess
import threading
import ipaddress
import tkinter as tk
from tkinter import ttk
from .base_tool import BaseTool


class NetworkDiscoveryTool(BaseTool):
    """Local network discovery tool."""
    
    def create_ui(self, parent):
        """Create the network discovery UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Network Discovery")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Network range input
        ttk.Label(input_frame, text="Network Range:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.range_var = ttk.StringVar(value="auto")
        ttk.Entry(input_frame, textvariable=self.range_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        # Auto-detect button
        ttk.Button(input_frame, text="Auto-Detect", command=self.auto_detect_network).grid(row=0, column=2, padx=5, pady=5)
        
        # Timeout
        ttk.Label(input_frame, text="Timeout (s):").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.timeout_var = ttk.StringVar(value="1")
        ttk.Entry(input_frame, textvariable=self.timeout_var, width=5).grid(row=0, column=4, padx=5, pady=5)
        
        # Scan button
        self.scan_btn = ttk.Button(input_frame, text="Scan", command=self.run_tool)
        self.scan_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # Stop button
        self.stop_btn = ttk.Button(input_frame, text="Stop", command=self.stop_scan, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=6, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def auto_detect_network(self):
        """Auto-detect local network range."""
        try:
            # Get local IP and subnet
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Try to get subnet mask from ipconfig
            result = subprocess.run(
                ['ipconfig'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Look for subnet mask
            subnet_mask = None
            for line in result.stdout.split('\n'):
                if 'Subnet Prefix' in line:
                    # Extract CIDR
                    import re
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)/(\d+)', line)
                    if match:
                        self.range_var.set(f"{match.group(1)}/{match.group(2)}")
                        return
            
            # Fallback: Assume /24 based on local IP
            parts = local_ip.split('.')
            parts[-1] = '0'
            network = '.'.join(parts)
            self.range_var.set(f"{network}/24")
        
        except Exception as e:
            self.append_output(f"Error auto-detecting network: {e}", 'ERROR')
    
    def run_tool(self):
        """Start network discovery."""
        network_range = self.range_var.get().strip()
        
        if not network_range or network_range == "auto":
            self.auto_detect_network()
            network_range = self.range_var.get().strip()
        
        if not network_range:
            self.append_output("Please specify a network range (e.g., 192.168.1.0/24).", 'ERROR')
            return
        
        try:
            timeout = float(self.timeout_var.get())
        except ValueError:
            timeout = 1.0
        
        self.clear_output()
        self.print_header(f"Network Discovery: {network_range}")
        self.append_output("Scanning network for active devices...", 'INFO')
        self.append_output("-" * 60, 'INFO')
        
        # Update button states
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start scan in thread
        self.run_in_thread(self._scan_network, args=(network_range, timeout))
    
    def _scan_network(self, network_range, timeout):
        """Scan network for active hosts."""
        try:
            self.gui.start_progress()
            
            # Parse network
            try:
                if '/' not in network_range:
                    network_range += '/24'
                
                network = ipaddress.IPv4Network(network_range, strict=False)
            except ValueError as e:
                self.append_output(f"Invalid network range: {e}", 'ERROR')
                return
            
            # Scan hosts
            hosts_found = []
            total = network.num_addresses
            scanned = 0
            
            self.append_output(f"Scanning {total} addresses (this may take a while)...", 'INFO')
            
            # Use threads for faster scanning
            threads = []
            max_threads = 50
            
            for ip in network.hosts():
                if self.stop_event.is_set():
                    self.append_output("\nScan cancelled by user.", 'WARNING')
                    break
                
                # Limit concurrent threads
                while len(threads) >= max_threads:
                    threads = [t for t in threads if t.is_alive()]
                
                scanned += 1
                if scanned % 50 == 0:
                    self.gui.set_status(f"Scanning: {scanned}/{total} hosts...")
                
                # Start thread for this host
                thread = threading.Thread(
                    target=self._ping_host,
                    args=(str(ip), timeout, hosts_found)
                )
                thread.start()
                threads.append(thread)
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Display results
            if not self.stop_event.is_set():
                self.append_output("\n" + "=" * 60, 'INFO')
                self.append_output(f"Scan complete! Found {len(hosts_found)} active device(s).", 'SUCCESS')
                self.append_output("=" * 60, 'INFO')
                
                if hosts_found:
                    self.append_output("\n--- Active Devices ---", 'INFO')
                    for ip, hostname in sorted(hosts_found):
                        if hostname:
                            self.append_output(f"  ✓ {ip} ({hostname})", 'SUCCESS')
                        else:
                            self.append_output(f"  ✓ {ip}", 'SUCCESS')
                
                # Get MAC addresses
                if hosts_found:
                    self.append_output("\n--- MAC Addresses (from ARP cache) ---", 'INFO')
                    self._get_mac_addresses([ip for ip, _ in hosts_found])
        
        except Exception as e:
            self.append_output(f"Error during scan: {e}", 'ERROR')
        finally:
            self.scan_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _ping_host(self, ip, timeout, results):
        """Ping a single host."""
        try:
            # Try TCP connection to common ports (faster than ICMP)
            for port in [80, 443, 22, 445]:
                if self.stop_event.is_set():
                    break
                
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    
                    if result == 0:
                        # Host is up, try to get hostname
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                        except:
                            hostname = None
                        
                        results.append((ip, hostname))
                        return
                except:
                    pass
            
            # Try ICMP ping as fallback
            try:
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', str(int(timeout * 1000)), ip],
                    capture_output=True,
                    text=True,
                    timeout=timeout + 1
                )
                
                if 'Reply from' in result.stdout:
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except:
                        hostname = None
                    
                    results.append((ip, hostname))
            
            except:
                pass
        
        except Exception:
            pass
    
    def _get_mac_addresses(self, ips):
        """Get MAC addresses from ARP cache."""
        try:
            # First, ping all IPs to populate ARP cache
            for ip in ips[:20]:  # Limit to 20
                subprocess.run(
                    ['ping', '-n', '1', '-w', '100', ip],
                    capture_output=True,
                    timeout=1
                )
            
            # Get ARP table
            result = subprocess.run(
                ['arp', '-a'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse ARP table
            for line in result.stdout.split('\n'):
                for ip in ips:
                    if ip in line:
                        # Extract MAC address
                        import re
                        mac_match = re.search(r'([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}', line)
                        if mac_match:
                            self.append_output(f"  {ip} -> {mac_match.group(0)}", 'INFO')
        
        except Exception as e:
            self.append_output(f"  Error getting MAC addresses: {e}", 'ERROR')
    
    def stop_scan(self):
        """Stop network scan."""
        self.stop_event.set()
        self.gui.set_status("Stopping scan...")
