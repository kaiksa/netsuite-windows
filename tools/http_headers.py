"""
HTTP Headers Inspector Tool for NetSuite GUI
Inspects HTTP response headers from web servers.
"""

import urllib.request
import urllib.error
from tkinter import ttk
from .base_tool import BaseTool


class HTTPHeadersTool(BaseTool):
    """HTTP headers inspector tool."""
    
    def create_ui(self, parent):
        """Create the HTTP headers UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="HTTP Headers Inspector")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # URL input
        ttk.Label(input_frame, text="URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_var = ttk.StringVar(value="https://www.example.com")
        ttk.Entry(input_frame, textvariable=self.url_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Method
        ttk.Label(input_frame, text="Method:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.method_var = ttk.StringVar(value="HEAD")
        ttk.Combobox(input_frame, textvariable=self.method_var, 
                    values=["HEAD", "GET"], width=8, 
                    state="readonly").grid(row=0, column=3, padx=5, pady=5)
        
        # User agent
        self.custom_ua_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(input_frame, text="Custom UA", variable=self.custom_ua_var).grid(row=0, column=4, padx=5, pady=5)
        
        # Inspect button
        ttk.Button(input_frame, text="Inspect Headers", command=self.run_tool).grid(row=0, column=5, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Inspect HTTP headers."""
        url = self.url_var.get().strip()
        
        if not url:
            self.append_output("Please enter a URL.", 'ERROR')
            return
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
        
        self.clear_output()
        self.print_header(f"HTTP Headers: {url}")
        
        self.run_in_thread(self._inspect_headers, args=(url,))
    
    def _inspect_headers(self, url):
        """Inspect HTTP headers."""
        try:
            self.gui.start_progress()
            self.gui.set_status(f"Fetching headers from {url}...")
            
            # Create request
            method = self.method_var.get()
            
            if method == "HEAD":
                request = urllib.request.Request(url, method='HEAD')
            else:
                request = urllib.request.Request(url, method='GET')
            
            # Add custom user agent if enabled
            if self.custom_ua_var.get():
                request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetSuite/1.0')
            
            # Make request
            with urllib.request.urlopen(request, timeout=10) as response:
                # Display response info
                self.append_output("\n--- Response Information ---", 'INFO')
                self.append_output(f"  Status: {response.status} {response.reason}", 'SUCCESS')
                self.append_output(f"  URL: {response.url}")
                
                # Display headers
                self.append_output("\n--- Response Headers ---", 'INFO')
                
                headers = dict(response.headers)
                
                # Group headers by category
                security_headers = [
                    'Strict-Transport-Security',
                    'Content-Security-Policy',
                    'X-Frame-Options',
                    'X-Content-Type-Options',
                    'X-XSS-Protection',
                    'Referrer-Policy'
                ]
                
                cache_headers = [
                    'Cache-Control',
                    'Expires',
                    'ETag',
                    'Last-Modified'
                ]
                
                # Security headers
                self.append_output("\n--- Security Headers ---", 'INFO')
                for header in security_headers:
                    if header in headers:
                        self.append_output(f"  {header}: {headers[header]}", 'SUCCESS')
                
                missing_security = [h for h in security_headers if h not in headers]
                if missing_security:
                    self.append_output(f"  Missing: {', '.join(missing_security)}", 'WARNING')
                
                # Cache headers
                self.append_output("\n--- Cache Headers ---", 'INFO')
                for header in cache_headers:
                    if header in headers:
                        self.append_output(f"  {header}: {headers[header]}")
                
                # Server information
                self.append_output("\n--- Server Information ---", 'INFO')
                if 'Server' in headers:
                    self.append_output(f"  Server: {headers['Server']}", 'SUCCESS')
                
                if 'X-Powered-By' in headers:
                    self.append_output(f"  X-Powered-By: {headers['X-Powered-By']}", 'WARNING')
                
                # Content information
                self.append_output("\n--- Content Information ---", 'INFO')
                if 'Content-Type' in headers:
                    self.append_output(f"  Content-Type: {headers['Content-Type']}", 'SUCCESS')
                
                if 'Content-Length' in headers:
                    self.append_output(f"  Content-Length: {headers['Content-Length']} bytes")
                
                if 'Content-Encoding' in headers:
                    self.append_output(f"  Content-Encoding: {headers['Content-Encoding']}")
                
                # Other headers
                other_headers = [h for h in headers.keys() 
                               if h not in security_headers + cache_headers + 
                               ['Server', 'X-Powered-By', 'Content-Type', 'Content-Length', 'Content-Encoding']]
                
                if other_headers:
                    self.append_output("\n--- Other Headers ---", 'INFO')
                    for header in sorted(other_headers):
                        self.append_output(f"  {header}: {headers[header]}")
                
                # Security assessment
                self.append_output("\n--- Security Assessment ---", 'INFO')
                self._assess_security(headers)
        
        except urllib.error.HTTPError as e:
            self.append_output(f"\nHTTP Error: {e.code} {e.reason}", 'ERROR')
            # Try to show headers even on error
            if e.headers:
                self.append_output("\nHeaders received:", 'INFO')
                for header, value in e.headers.items():
                    self.append_output(f"  {header}: {value}")
        except urllib.error.URLError as e:
            self.append_output(f"\nURL Error: {e.reason}", 'ERROR')
        except Exception as e:
            self.append_output(f"\nError: {e}", 'ERROR')
        finally:
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _assess_security(self, headers):
        """Assess security headers."""
        score = 0
        max_score = 6
        
        checks = [
            ('Strict-Transport-Security', 'HSTS enabled'),
            ('X-Frame-Options', 'Clickjacking protection'),
            ('X-Content-Type-Options', 'MIME sniffing protection'),
            ('Content-Security-Policy', 'CSP enabled'),
            ('X-XSS-Protection', 'XSS filter'),
            ('Referrer-Policy', 'Referrer policy set')
        ]
        
        for header, description in checks:
            if header in headers:
                self.append_output(f"  ✓ {description}", 'SUCCESS')
                score += 1
            else:
                self.append_output(f"  ✗ Missing: {header}", 'WARNING')
        
        self.append_output(f"\n  Security Score: {score}/{max_score}", 'INFO' if score >= 4 else 'WARNING')
