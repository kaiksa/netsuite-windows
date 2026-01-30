"""
IP Geolocation Tool for NetSuite GUI
Provides geographical information for IP addresses.
"""

import urllib.request
import json
import re
import tkinter as tk
from tkinter import ttk
from .base_tool import BaseTool


class IPGeolocationTool(BaseTool):
    """IP geolocation lookup tool using free web APIs."""
    
    def create_ui(self, parent):
        """Create the IP geolocation UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="IP Geolocation")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # IP input
        ttk.Label(input_frame, text="IP Address:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ip_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.ip_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        # My IP button
        ttk.Button(input_frame, text="My IP", command=self.get_my_ip).grid(row=0, column=2, padx=5, pady=5)
        
        # Lookup button
        ttk.Button(input_frame, text="Lookup", command=self.run_tool).grid(row=0, column=3, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def get_my_ip(self):
        """Get and set the user's public IP."""
        try:
            # Get public IP
            ip = self._get_public_ip()
            if ip:
                self.ip_var.set(ip)
            else:
                self.append_output("Failed to get public IP.", 'ERROR')
        except Exception as e:
            self.append_output(f"Error: {e}", 'ERROR')
    
    def run_tool(self):
        """Perform IP geolocation lookup."""
        ip = self.ip_var.get().strip()
        
        if not ip:
            self.append_output("Please enter an IP address.", 'ERROR')
            return
        
        if not self._is_valid_ip(ip):
            self.append_output("Invalid IP address format.", 'ERROR')
            return
        
        self.clear_output()
        self.print_header(f"IP Geolocation: {ip}")
        
        self.run_in_thread(self._lookup_ip, args=(ip,))
    
    def _lookup_ip(self, ip):
        """Lookup IP geolocation."""
        try:
            self.gui.start_progress()
            self.gui.set_status(f"Looking up {ip}...")
            
            # Try ip-api.com (free, no key needed)
            data = self._query_ip_api(ip)
            
            if data:
                self._display_geolocation(data)
            else:
                self.append_output("Failed to retrieve geolocation data.", 'ERROR')
        
        except Exception as e:
            self.append_output(f"Error during lookup: {e}", 'ERROR')
        finally:
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _query_ip_api(self, ip):
        """Query ip-api.com for geolocation data."""
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
            
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if data.get('status') == 'success':
                    return data
                else:
                    return None
        
        except Exception as e:
            return None
    
    def _display_geolocation(self, data):
        """Display geolocation information."""
        self.append_output("\n--- Location Information ---", 'INFO')
        
        if 'country' in data:
            self.append_output(f"  Country: {data.get('country', 'N/A')}", 'SUCCESS')
            self.append_output(f"  Country Code: {data.get('countryCode', 'N/A')}")
        
        if 'regionName' in data:
            self.append_output(f"  Region: {data.get('regionName', 'N/A')}")
            self.append_output(f"  Region Code: {data.get('region', 'N/A')}")
        
        if 'city' in data:
            self.append_output(f"  City: {data.get('city', 'N/A')}")
        
        if 'zip' in data:
            self.append_output(f"  Postal Code: {data.get('zip', 'N/A')}")
        
        if 'lat' in data and 'lon' in data:
            self.append_output(f"  Coordinates: {data.get('lat')}, {data.get('lon')}")
            self.append_output(f"  Google Maps: https://www.google.com/maps?q={data.get('lat')},{data.get('lon')}", 'INFO')
        
        self.append_output("\n--- Network Information ---", 'INFO')
        
        if 'isp' in data:
            self.append_output(f"  ISP: {data.get('isp', 'N/A')}")
        
        if 'org' in data:
            self.append_output(f"  Organization: {data.get('org', 'N/A')}")
        
        if 'as' in data:
            self.append_output(f"  AS: {data.get('as', 'N/A')}")
        
        if 'timezone' in data:
            self.append_output(f"  Timezone: {data.get('timezone', 'N/A')}")
        
        self.append_output("\n--- Raw Data ---", 'INFO')
        for key, value in data.items():
            if key not in ['status']:
                self.append_output(f"  {key}: {value}")
    
    def _get_public_ip(self):
        """Get the user's public IP address."""
        try:
            with urllib.request.urlopen('https://api.ipify.org?format=text', timeout=5) as response:
                return response.read().decode()
        except:
            return None
    
    def _is_valid_ip(self, s):
        """Check if string is a valid IP address."""
        try:
            parts = s.split('.')
            return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
        except:
            return False
