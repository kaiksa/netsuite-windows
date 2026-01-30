"""
DNS Lookup Tool for NetSuite GUI
Performs DNS lookups and displays various DNS record types.
"""

import socket
import subprocess
import re
from tkinter import ttk
from .base_tool import BaseTool


class DNSLookupTool(BaseTool):
    """DNS Lookup and DNS record query tool."""
    
    def create_ui(self, parent):
        """Create the DNS lookup UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="DNS Lookup")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Domain input
        ttk.Label(input_frame, text="Domain:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.domain_var = ttk.StringVar(value="example.com")
        ttk.Entry(input_frame, textvariable=self.domain_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Record type selector
        ttk.Label(input_frame, text="Record Type:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.record_type_var = ttk.StringVar(value="A")
        record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "PTR"]
        ttk.Combobox(input_frame, textvariable=self.record_type_var, values=record_types, 
                    width=10, state="readonly").grid(row=0, column=3, padx=5, pady=5)
        
        # Lookup button
        ttk.Button(input_frame, text="Lookup", command=self.run_tool).grid(row=0, column=4, padx=5, pady=5)
        
        # Advanced options
        adv_frame = ttk.Frame(input_frame)
        adv_frame.grid(row=1, column=0, columnspan=5, sticky=tk.W, padx=5, pady=5)
        
        self.dns_server_var = ttk.StringVar(value="")
        ttk.Label(adv_frame, text="DNS Server (optional):").pack(side=tk.LEFT)
        ttk.Entry(adv_frame, textvariable=self.dns_server_var, width=20).pack(side=tk.LEFT, padx=5)
        
        # All records button
        ttk.Button(adv_frame, text="Query All Records", command=self.query_all_records).pack(side=tk.LEFT, padx=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Perform DNS lookup."""
        domain = self.domain_var.get().strip()
        record_type = self.record_type_var.get()
        
        if not domain:
            self.append_output("Please enter a domain name.", 'ERROR')
            return
        
        self.clear_output()
        self.print_header(f"DNS Lookup: {domain} ({record_type})")
        
        def lookup():
            try:
                self.gui.start_progress()
                self.gui.set_status(f"Looking up {record_type} record for {domain}...")
                
                # Use nslookup command on Windows
                result = self._nslookup(domain, record_type)
                
                if result:
                    self.append_output(result, 'SUCCESS')
                else:
                    self.append_output("No records found or lookup failed.", 'WARNING')
                
                # Additional info using socket for A records
                if record_type in ['A', 'AAAA']:
                    self.append_output("\n--- Socket Resolution ---", 'INFO')
                    try:
                        ips = socket.getaddrinfo(domain, None)
                        seen = set()
                        for ip in ips:
                            addr = ip[4][0]
                            if addr not in seen:
                                self.append_output(f"  {addr}", 'SUCCESS')
                                seen.add(addr)
                    except socket.gaierror as e:
                        self.append_output(f"Error: {e}", 'ERROR')
                
            except Exception as e:
                self.append_output(f"Error during lookup: {e}", 'ERROR')
            finally:
                self.gui.stop_progress()
                self.gui.set_status("Ready")
        
        self.run_in_thread(lookup)
    
    def query_all_records(self):
        """Query all common record types."""
        domain = self.domain_var.get().strip()
        
        if not domain:
            self.append_output("Please enter a domain name.", 'ERROR')
            return
        
        self.clear_output()
        self.print_header(f"DNS Lookup: All Records for {domain}")
        
        def lookup_all():
            record_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA"]
            
            try:
                self.gui.start_progress()
                
                for record_type in record_types:
                    self.gui.set_status(f"Querying {record_type} records...")
                    self.append_output(f"\n--- {record_type} Records ---", 'INFO')
                    
                    result = self._nslookup(domain, record_type)
                    if result:
                        self.append_output(result, 'SUCCESS')
                    else:
                        self.append_output("  No records found", 'WARNING')
            
            except Exception as e:
                self.append_output(f"Error: {e}", 'ERROR')
            finally:
                self.gui.stop_progress()
                self.gui.set_status("Ready")
        
        self.run_in_thread(lookup_all)
    
    def _nslookup(self, domain, record_type):
        """Perform nslookup using Windows nslookup command."""
        try:
            # Build nslookup command
            cmd = ['nslookup', '-type=' + record_type, domain]
            
            dns_server = self.dns_server_var.get().strip()
            if dns_server:
                cmd.append(dns_server)
            
            # Run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout + result.stderr
            
            # Parse and format output
            lines = output.split('\n')
            formatted = []
            
            in_answer = False
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and headers
                if not line or 'Non-authoritative' in line:
                    continue
                
                # Look for answer section
                if 'answer:' in line.lower() or 'answers:' in line.lower():
                    in_answer = True
                    continue
                
                # Parse records
                if in_answer or domain in line:
                    # Clean up the line
                    if record_type == 'MX':
                        match = re.search(r'mail exchanger = (\d+) (.+)', line)
                        if match:
                            formatted.append(f"  Priority: {match.group(1)}, Mail Server: {match.group(2)}")
                    elif record_type in ['A', 'AAAA']:
                        match = re.search(r'Name:.*?\nAddress(?:es)?:\s*([\d.:]+)', output, re.DOTALL)
                        if match:
                            for addr in match.group(1).split():
                                if addr and addr != line:
                                    formatted.append(f"  {addr}")
                    elif record_type == 'TXT':
                        if 'text =' in line or '"' in line:
                            formatted.append(f"  {line}")
                    else:
                        if line and not line.startswith('nslookup') and 'Server:' not in line:
                            formatted.append(f"  {line}")
            
            # If nslookup parsing failed, try to extract IPs directly
            if not formatted:
                if record_type in ['A', 'AAAA']:
                    try:
                        addr = socket.gethostbyname(domain)
                        formatted.append(f"  {addr}")
                    except:
                        pass
                else:
                    # Fallback to raw output
                    for line in lines:
                        if line.strip() and 'Server:' not in line and 'nslookup' not in line.lower():
                            formatted.append(f"  {line.strip()}")
            
            return '\n'.join(formatted) if formatted else None
            
        except subprocess.TimeoutExpired:
            return "Lookup timed out"
        except Exception as e:
            return f"Error: {str(e)}"
