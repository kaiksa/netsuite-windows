"""
Port Scanner Tool for NetSuite GUI
Scans for open ports on a target host.
"""

import socket
import subprocess
import threading
from tkinter import ttk
from .base_tool import BaseTool


class PortScannerTool(BaseTool):
    """Port scanner for detecting open ports and services."""
    
    # Common ports to scan
    COMMON_PORTS = [
        21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 
        1433, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 8888, 27017
    ]
    
    # Well-known service names
    SERVICE_NAMES = {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
        80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 445: 'SMB',
        993: 'IMAPS', 995: 'POP3S', 1433: 'MSSQL', 3306: 'MySQL',
        3389: 'RDP', 5432: 'PostgreSQL', 5900: 'VNC', 6379: 'Redis',
        8080: 'HTTP-Alt', 8443: 'HTTPS-Alt', 8888: 'HTTP-Alt', 27017: 'MongoDB'
    }
    
    def create_ui(self, parent):
        """Create the port scanner UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Port Scanner")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Host input
        ttk.Label(input_frame, text="Host/IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.host_var = ttk.StringVar(value="127.0.0.1")
        ttk.Entry(input_frame, textvariable=self.host_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        
        # Scan type
        ttk.Label(input_frame, text="Scan:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.scan_type_var = ttk.StringVar(value="common")
        scan_frame = ttk.Frame(input_frame)
        scan_frame.grid(row=0, column=3, columnspan=2, sticky=tk.W)
        
        ttk.Radiobutton(scan_frame, text="Common Ports", variable=self.scan_type_var, 
                       value="common").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(scan_frame, text="Port Range", variable=self.scan_type_var, 
                       value="range").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(scan_frame, text="Single Port", variable=self.scan_type_var, 
                       value="single").pack(side=tk.LEFT, padx=2)
        
        # Port range inputs
        ttk.Label(input_frame, text="From:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.port_from_var = ttk.StringVar(value="1")
        ttk.Entry(input_frame, textvariable=self.port_from_var, width=8).grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(input_frame, text="To:").grid(row=1, column=4, padx=5, pady=5, sticky=tk.W)
        self.port_to_var = ttk.StringVar(value="1024")
        ttk.Entry(input_frame, textvariable=self.port_to_var, width=8).grid(row=1, column=5, padx=5, pady=5, sticky=tk.W)
        
        # Timeout
        ttk.Label(input_frame, text="Timeout (s):").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        self.timeout_var = ttk.StringVar(value="1")
        ttk.Entry(input_frame, textvariable=self.timeout_var, width=5).grid(row=0, column=7, padx=5, pady=5)
        
        # Scan button
        self.scan_btn = ttk.Button(input_frame, text="Scan", command=self.run_tool)
        self.scan_btn.grid(row=0, column=8, padx=5, pady=5)
        
        # Stop button
        self.stop_btn = ttk.Button(input_frame, text="Stop", command=self.stop_scan, state=tk.DISABLED)
        self.stop_btn.grid(row=1, column=8, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Start port scan."""
        host = self.host_var.get().strip()
        
        if not host:
            self.append_output("Please enter a host or IP address.", 'ERROR')
            return
        
        # Determine ports to scan
        scan_type = self.scan_type_var.get()
        
        if scan_type == "common":
            ports = self.COMMON_PORTS
        elif scan_type == "range":
            try:
                port_from = int(self.port_from_var.get())
                port_to = int(self.port_to_var.get())
                if port_from < 1 or port_to > 65535 or port_from > port_to:
                    raise ValueError()
                ports = range(port_from, port_to + 1)
            except ValueError:
                self.append_output("Invalid port range. Use 1-65535.", 'ERROR')
                return
        else:  # single
            try:
                port = int(self.port_from_var.get())
                if port < 1 or port > 65535:
                    raise ValueError()
                ports = [port]
            except ValueError:
                self.append_output("Invalid port number. Use 1-65535.", 'ERROR')
                return
        
        try:
            timeout = float(self.timeout_var.get())
        except ValueError:
            timeout = 1.0
        
        self.clear_output()
        self.print_header(f"Port Scan: {host}")
        self.append_output(f"Scanning {len(ports) if isinstance(ports, list) else f'{ports.start}-{ports.stop-1'} ports...", 'INFO')
        self.append_output("-" * 50, 'INFO')
        
        # Update button states
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start scan in thread
        self.run_in_thread(self._scan_thread, args=(host, ports, timeout))
    
    def _scan_thread(self, host, ports, timeout):
        """Port scanning thread."""
        try:
            self.gui.start_progress()
            
            open_ports = []
            total = len(ports) if isinstance(ports, list) else (ports.stop - ports.start)
            scanned = 0
            
            for port in ports:
                if self.stop_event.is_set():
                    self.append_output("\nScan cancelled by user.", 'WARNING')
                    break
                
                scanned += 1
                if scanned % 10 == 0 or isinstance(ports, list):
                    self.gui.set_status(f"Scanning: {scanned}/{total} ports...")
                
                # Scan port
                result = self._scan_port(host, port, timeout)
                
                if result['open']:
                    open_ports.append(port)
                    service = self.SERVICE_NAMES.get(port, 'Unknown')
                    self.append_output(f"Port {port:5d}/tcp - OPEN - {service}", 'SUCCESS')
                
                # Also try to grab banner for common service ports
                if result['open'] and port in [21, 22, 25, 80, 110, 143, 443, 3306, 3389, 8080]:
                    banner = self._grab_banner(host, port, timeout)
                    if banner:
                        self.append_output(f"         Banner: {banner[:100]}", 'INFO')
            
            # Summary
            if not self.stop_event.is_set():
                self.append_output("\n" + "=" * 50, 'INFO')
                self.append_output(f"Scan complete! Found {len(open_ports)} open port(s).", 'SUCCESS')
                self.append_output("=" * 50, 'INFO')
        
        except Exception as e:
            self.append_output(f"Error during scan: {e}", 'ERROR')
        finally:
            self.scan_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _scan_port(self, host, port, timeout):
        """Scan a single port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = {'open': False, 'error': None}
        
        try:
            result_open = sock.connect_ex((host, port))
            result['open'] = (result_open == 0)
        except socket.gaierror:
            result['error'] = "Hostname resolution failed"
        except socket.error:
            result['error'] = "Could not connect"
        finally:
            sock.close()
        
        return result
    
    def _grab_banner(self, host, port, timeout):
        """Attempt to grab service banner."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            sock.connect((host, port))
            
            # Send simple probe
            if port == 80 or port == 8080:
                sock.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
            elif port in [21, 25, 110, 143]:
                # Wait for server banner
                pass
            else:
                sock.send(b"\r\n")
            
            # Receive response
            try:
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                if banner and len(banner) > 0:
                    return banner.split('\n')[0]  # First line only
            except:
                pass
            
            sock.close()
        except:
            pass
        
        return None
    
    def stop_scan(self):
        """Stop port scan."""
        self.stop_event.set()
        self.gui.set_status("Stopping scan...")


def scan_port_multi(host, port, timeout):
    """Scan a single port (for use in thread pool)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        return (port, result == 0)
    except:
        sock.close()
        return (port, False)
