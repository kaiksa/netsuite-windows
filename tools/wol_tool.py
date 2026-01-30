"""
Wake-on-LAN Tool for NetSuite GUI
Sends magic packets to wake up remote devices.
"""

import socket
import struct
import re
from tkinter import ttk
from .base_tool import BaseTool


class WakeOnLanTool(BaseTool):
    """Wake-on-LAN magic packet sender."""
    
    def create_ui(self, parent):
        """Create the Wake-on-LAN UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Wake-on-LAN")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # MAC address input
        ttk.Label(input_frame, text="MAC Address:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.mac_var = ttk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.mac_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        # Broadcast address
        ttk.Label(input_frame, text="Broadcast IP:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.broadcast_var = ttk.StringVar(value="255.255.255.255")
        ttk.Entry(input_frame, textvariable=self.broadcast_var, width=15).grid(row=0, column=3, padx=5, pady=5)
        
        # Port
        ttk.Label(input_frame, text="Port:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.port_var = ttk.StringVar(value="9")
        ttk.Entry(input_frame, textvariable=self.port_var, width=6).grid(row=0, column=5, padx=5, pady=5)
        
        # Send button
        ttk.Button(input_frame, text="Send Magic Packet", command=self.run_tool).grid(row=0, column=6, padx=5, pady=5)
        
        # History frame
        history_frame = ttk.LabelFrame(parent, text="Saved MAC Addresses")
        history_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # MAC history list
        self.mac_history = []
        
        # Name input
        ttk.Label(history_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.name_var = ttk.StringVar(value="")
        ttk.Entry(history_frame, textvariable=self.name_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        # Save button
        ttk.Button(history_frame, text="Save", command=self.save_mac).grid(row=0, column=2, padx=5, pady=5)
        
        # History listbox
        self.history_listbox = tk.Listbox(history_frame, height=4)
        self.history_listbox.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        
        # Load button
        ttk.Button(history_frame, text="Load Selected", command=self.load_mac).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(history_frame, text="Remove", command=self.remove_mac).grid(row=2, column=1, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Send Wake-on-LAN magic packet."""
        mac_address = self.mac_var.get().strip()
        broadcast_ip = self.broadcast_var.get().strip()
        
        try:
            port = int(self.port_var.get())
        except ValueError:
            self.append_output("Invalid port number.", 'ERROR')
            return
        
        if not mac_address:
            self.append_output("Please enter a MAC address.", 'ERROR')
            return
        
        if not self._is_valid_mac(mac_address):
            self.append_output("Invalid MAC address format. Use XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX", 'ERROR')
            return
        
        self.clear_output()
        self.print_header(f"Wake-on-LAN: {mac_address}")
        
        self.run_in_thread(self._send_wol_packet, args=(mac_address, broadcast_ip, port))
    
    def _send_wol_packet(self, mac_address, broadcast_ip, port):
        """Send Wake-on-LAN magic packet."""
        try:
            self.gui.start_progress()
            self.gui.set_status(f"Sending magic packet to {mac_address}...")
            
            # Clean MAC address
            mac_address = mac_address.replace('-', ':').upper()
            
            self.append_output(f"\n--- Wake-on-LAN Packet ---", 'INFO')
            self.append_output(f"  Target MAC: {mac_address}")
            self.append_output(f"  Broadcast: {broadcast_ip}:{port}")
            
            # Create magic packet
            # 6 bytes of FF followed by MAC repeated 16 times
            mac_bytes = bytes.fromhex(mac_address.replace(':', ''))
            magic_packet = b'\xff' * 6 + mac_bytes * 16
            
            # Send packet
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            self.append_output(f"  Packet size: {len(magic_packet)} bytes")
            self.append_output(f"  Sending...", 'INFO')
            
            sock.sendto(magic_packet, (broadcast_ip, port))
            sock.close()
            
            self.append_output(f"\n✓ Magic packet sent successfully!", 'SUCCESS')
            self.append_output(f"\nNote: The device may take a few seconds to several minutes to wake up.", 'INFO')
            self.append_output(f"Make sure WOL is enabled in the device's BIOS/UEFI and network settings.", 'INFO')
            
            # Add to recent history temporarily
            if mac_address not in [m['mac'] for m in self.mac_history]:
                name = self.name_var.get().strip() or f"Device {len(self.mac_history) + 1}"
                self.mac_history.append({'mac': mac_address, 'name': name})
                self._update_history_list()
        
        except Exception as e:
            self.append_output(f"\nError sending magic packet: {e}", 'ERROR')
        finally:
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _is_valid_mac(self, mac):
        """Check if MAC address is valid."""
        # Remove separators
        mac_clean = mac.replace('-', ':').replace('.', '')
        
        # Check format
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac.replace('-', ':')):
            return False
        
        return True
    
    def save_mac(self):
        """Save MAC address to history."""
        mac = self.mac_var.get().strip()
        name = self.name_var.get().strip()
        
        if not mac or not self._is_valid_mac(mac):
            self.append_output("Invalid MAC address.", 'ERROR')
            return
        
        if not name:
            name = f"Device {len(self.mac_history) + 1}"
        
        # Check if already exists
        for entry in self.mac_history:
            if entry['mac'] == mac:
                entry['name'] = name
                self._update_history_list()
                return
        
        # Add new entry
        self.mac_history.append({'mac': mac, 'name': name})
        self._update_history_list()
    
    def load_mac(self):
        """Load selected MAC from history."""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.mac_history):
                entry = self.mac_history[index]
                self.mac_var.set(entry['mac'])
                self.name_var.set(entry['name'])
    
    def remove_mac(self):
        """Remove selected MAC from history."""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.mac_history):
                del self.mac_history[index]
                self._update_history_list()
    
    def _update_history_list(self):
        """Update the history listbox."""
        self.history_listbox.delete(0, tk.END)
        for entry in self.mac_history:
            self.history_listbox.insert(tk.END, f"{entry['name']} - {entry['mac']}")
