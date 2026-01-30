"""
WHOIS Tool for NetSuite GUI
Performs WHOIS lookups for domain and IP information.
"""

import subprocess
import re
import tkinter as tk
from tkinter import ttk
from .base_tool import BaseTool


class WHOISTool(BaseTool):
    """WHOIS lookup tool using Windows whois or web services."""
    
    def create_ui(self, parent):
        """Create the WHOIS UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="WHOIS Lookup")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Query input
        ttk.Label(input_frame, text="Domain/IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.query_var = tk.StringVar(value="example.com")
        ttk.Entry(input_frame, textvariable=self.query_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Lookup button
        ttk.Button(input_frame, text="Lookup", command=self.run_tool).grid(row=0, column=2, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Perform WHOIS lookup."""
        query = self.query_var.get().strip()
        
        if not query:
            self.append_output("Please enter a domain or IP address.", 'ERROR')
            return
        
        self.clear_output()
        self.print_header(f"WHOIS: {query}")
        
        self.run_in_thread(self._whois_lookup, args=(query,))
    
    def _whois_lookup(self, query):
        """Perform WHOIS lookup."""
        try:
            self.gui.start_progress()
            self.gui.set_status(f"Looking up {query}...")
            
            # Try using whois command if available
            result = self._whois_command(query)
            
            if result:
                self._format_whois(result)
            else:
                # Fallback to web-based WHOIS
                self.append_output("Note: Using web-based WHOIS lookup", 'INFO')
                self._web_whois(query)
        
        except Exception as e:
            self.append_output(f"Error during lookup: {e}", 'ERROR')
        finally:
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _whois_command(self, query):
        """Try using whois command."""
        try:
            # Check if whois is available
            result = subprocess.run(
                ['whois', query],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                return result.stdout
        except FileNotFoundError:
            return None
        except Exception:
            return None
    
    def _web_whois(self, query):
        """Use web-based WHOIS lookup."""
        import urllib.request
        import urllib.parse
        
        try:
            # Use whois.com API
            url = f"https://www.whois.com/whois/{query}"
            
            self.append_output(f"WHOIS information for {query}:", 'INFO')
            self.append_output("-" * 50, 'INFO')
            self.append_output("Full WHOIS data available at:", 'INFO')
            self.append_output(f"  {url}", 'SUCCESS')
            self.append_output("\nNote: For complete WHOIS information, visit the URL above or use a dedicated WHOIS client.", 'WARNING')
            
        except Exception as e:
            self.append_output(f"Web lookup failed: {e}", 'ERROR')
    
    def _format_whois(self, data):
        """Format WHOIS output for display."""
        # Parse and highlight important fields
        important_fields = [
            'Domain Name', 'Registry Domain ID', 'Registrar', 'Created Date',
            'Updated Date', 'Expiry Date', 'Name Server', 'Registrant',
            'Admin', 'Tech', 'Status', 'Organization'
        ]
        
        lines = data.split('\n')
        in_important_section = False
        
        for line in lines:
            line = line.rstrip()
            
            # Check for important fields
            is_important = False
            for field in important_fields:
                if line.startswith(field) or line.startswith(f'{field}:'):
                    is_important = True
                    in_important_section = True
                    break
            
            if is_important:
                self.append_output(line, 'SUCCESS')
            elif in_important_section and line.strip():
                self.append_output(f"  {line}", 'INFO')
            elif line.startswith('>>>'):
                self.append_output(line, 'INFO')
                in_important_section = False
            elif line.strip() == '%':
                self.append_output(line, 'INFO')
