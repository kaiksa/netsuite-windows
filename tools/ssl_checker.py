"""
SSL/TLS Certificate Checker Tool for NetSuite GUI
Checks SSL/TLS certificates for HTTPS sites.
"""

import ssl
import socket
import datetime
import tkinter as tk
from tkinter import ttk
from .base_tool import BaseTool


class SSLCheckerTool(BaseTool):
    """SSL/TLS certificate checker."""
    
    def create_ui(self, parent):
        """Create the SSL checker UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="SSL/TLS Certificate Checker")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Host input
        ttk.Label(input_frame, text="Host:Port:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.host_var = tk.StringVar(value="google.com:443")
        ttk.Entry(input_frame, textvariable=self.host_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Check button
        ttk.Button(input_frame, text="Check Certificate", command=self.run_tool).grid(row=0, column=2, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Check SSL certificate."""
        host_input = self.host_var.get().strip()
        
        if not host_input:
            self.append_output("Please enter a host:port (e.g., google.com:443).", 'ERROR')
            return
        
        # Parse host and port
        if ':' in host_input:
            host, port = host_input.split(':', 1)
            try:
                port = int(port)
            except ValueError:
                self.append_output("Invalid port number.", 'ERROR')
                return
        else:
            host = host_input
            port = 443
        
        self.clear_output()
        self.print_header(f"SSL/TLS Certificate: {host}:{port}")
        
        self.run_in_thread(self._check_certificate, args=(host, port))
    
    def _check_certificate(self, host, port):
        """Check SSL certificate."""
        try:
            self.gui.start_progress()
            self.gui.set_status(f"Checking certificate for {host}:{port}...")
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to server
            with socket.create_connection((host, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Display certificate information
                    self._display_cert_info(host, cert)
                    
                    # Check expiration
                    self._check_expiration(cert)
                    
                    # Check issuer
                    self._check_issuer(cert)
                    
                    # Display subject
                    self._display_subject(cert)
                    
                    # Display SANs
                    self._display_sans(cert)
        
        except ssl.SSLCertVerificationError as e:
            self.append_output(f"\nCertificate Verification Error: {e}", 'ERROR')
            self.append_output("The certificate may be expired or self-signed.", 'WARNING')
        except socket.timeout:
            self.append_output("Connection timed out.", 'ERROR')
        except socket.gaierror:
            self.append_output("Failed to resolve hostname.", 'ERROR')
        except Exception as e:
            self.append_output(f"Error: {e}", 'ERROR')
        finally:
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _display_cert_info(self, host, cert):
        """Display basic certificate information."""
        self.append_output("\n--- Certificate Information ---", 'INFO')
        
        # Version
        version = cert.get('version')
        if version:
            self.append_output(f"  Version: {version}", 'SUCCESS')
        
        # Serial number
        serial = cert.get('serialNumber')
        if serial:
            self.append_output(f"  Serial Number: {serial}")
        
        # Valid from
        not_before = cert.get('notBefore')
        if not_before:
            self.append_output(f"  Valid From: {not_before}")
        
        # Valid to
        not_after = cert.get('notAfter')
        if not_after:
            self.append_output(f"  Valid To: {not_after}")
    
    def _check_expiration(self, cert):
        """Check certificate expiration."""
        self.append_output("\n--- Expiration Status ---", 'INFO')
        
        not_after = cert.get('notAfter')
        if not not_after:
            self.append_output("  Unable to determine expiration date.", 'WARNING')
            return
        
        # Parse date
        try:
            # Format: May 25 12:00:00 2024 GMT
            exp_date = datetime.datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            now = datetime.datetime.now(exp_date.tzinfo)
            
            days_left = (exp_date - now).days
            
            if days_left < 0:
                self.append_output(f"  Status: EXPIRED ({abs(days_left)} days ago)", 'ERROR')
            elif days_left < 7:
                self.append_output(f"  Status: EXPIRING SOON ({days_left} days left)", 'ERROR')
            elif days_left < 30:
                self.append_output(f"  Status: Expiring in {days_left} days", 'WARNING')
            else:
                self.append_output(f"  Status: Valid ({days_left} days remaining)", 'SUCCESS')
        
        except Exception as e:
            self.append_output(f"  Error parsing expiration: {e}", 'ERROR')
    
    def _check_issuer(self, cert):
        """Display certificate issuer."""
        self.append_output("\n--- Issuer ---", 'INFO')
        
        issuer = cert.get('issuer')
        if issuer:
            for item in issuer:
                key, value = item[0]
                self.append_output(f"  {key}: {value}")
    
    def _display_subject(self, cert):
        """Display certificate subject."""
        self.append_output("\n--- Subject ---", 'INFO')
        
        subject = cert.get('subject')
        if subject:
            for item in subject:
                key, value = item[0]
                self.append_output(f"  {key}: {value}")
    
    def _display_sans(self, cert):
        """Display Subject Alternative Names."""
        self.append_output("\n--- Subject Alternative Names ---", 'INFO')
        
        # SANs are in the extensions
        extensions = cert.get('extensions', [])
        
        for ext in extensions:
            if 'subjectAltName' in str(ext):
                # Parse SANs
                san_list = []
                for item in ext:
                    if isinstance(item, tuple):
                        for name in item:
                            if isinstance(name, tuple):
                                san_list.append(f"{name[0]}:{name[1]}")
                
                if san_list:
                    for san in san_list:
                        self.append_output(f"  {san}", 'SUCCESS')
                else:
                    # Try to parse as string
                    try:
                        sans = str(ext).split(', ')
                        for san in sans:
                            if san.strip():
                                self.append_output(f"  {san}", 'SUCCESS')
                    except:
                        pass
                
                return
        
        self.append_output("  No SANs found", 'WARNING')
