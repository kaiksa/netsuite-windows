"""
Subnet Calculator Tool for NetSuite GUI
Calculates network information from IP/CIDR.
"""

import ipaddress
from tkinter import ttk
from .base_tool import BaseTool


class SubnetCalculatorTool(BaseTool):
    """Subnet calculator for IPv4 networks."""
    
    def create_ui(self, parent):
        """Create the subnet calculator UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Subnet Calculator")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # IP/CIDR input
        ttk.Label(input_frame, text="Network (IP/CIDR):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.network_var = ttk.StringVar(value="192.168.1.0/24")
        ttk.Entry(input_frame, textvariable=self.network_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        
        # Calculate button
        ttk.Button(input_frame, text="Calculate", command=self.run_tool).grid(row=0, column=2, padx=5, pady=5)
        
        # Common subnets quick buttons
        quick_frame = ttk.Frame(input_frame)
        quick_frame.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(quick_frame, text="/24", width=4, 
                  command=lambda: self.network_var.set("192.168.1.0/24")).pack(side=tk.LEFT, padx=1)
        ttk.Button(quick_frame, text="/25", width=4,
                  command=lambda: self.network_var.set("192.168.1.0/25")).pack(side=tk.LEFT, padx=1)
        ttk.Button(quick_frame, text="/26", width=4,
                  command=lambda: self.network_var.set("192.168.1.0/26")).pack(side=tk.LEFT, padx=1)
        ttk.Button(quick_frame, text="/30", width=4,
                  command=lambda: self.network_var.set("192.168.1.0/30")).pack(side=tk.LEFT, padx=1)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Calculate subnet information."""
        network_str = self.network_var.get().strip()
        
        if not network_str:
            self.append_output("Please enter a network in CIDR notation (e.g., 192.168.1.0/24).", 'ERROR')
            return
        
        self.clear_output()
        self.print_header(f"Subnet Calculator: {network_str}")
        
        try:
            # Parse network
            network = ipaddress.IPv4Network(network_str, strict=False)
            
            # Display network information
            self._display_network_info(network)
            
            # Display address ranges
            self._display_address_ranges(network)
            
            # Display subnet masks
            self._display_subnet_masks(network)
            
            # Display host details (for small networks)
            if network.num_addresses <= 256:
                self._display_hosts(network)
        
        except ValueError as e:
            self.append_output(f"Invalid network: {e}", 'ERROR')
        except Exception as e:
            self.append_output(f"Error: {e}", 'ERROR')
    
    def _display_network_info(self, network):
        """Display basic network information."""
        self.append_output("\n--- Network Information ---", 'INFO')
        self.append_output(f"  Network Address: {network.network_address}", 'SUCCESS')
        self.append_output(f"  Broadcast Address: {network.broadcast_address}")
        self.append_output(f"  Netmask: {network.netmask}")
        self.append_output(f"  Wildcard Mask: {network.hostmask}")
        self.append_output(f"  CIDR Notation: /{network.prefixlen}")
        self.append_output(f"  Total Addresses: {network.num_addresses}")
        self.append_output(f"  Usable Hosts: {network.num_addresses - 2}")
        self.append_output(f"  First Usable: {list(network.hosts())[0] if network.num_addresses > 2 else 'N/A'}")
        self.append_output(f"  Last Usable: {list(network.hosts())[-1] if network.num_addresses > 2 else 'N/A'}")
    
    def _display_address_ranges(self, network):
        """Display address ranges."""
        self.append_output("\n--- Address Ranges ---", 'INFO')
        
        if network.num_addresses == 1:
            self.append_output(f"  Single Address: {network.network_address}")
        elif network.num_addresses == 2:
            self.append_output(f"  Network: {network.network_address}")
            self.append_output(f"  Broadcast: {network.broadcast_address}")
        else:
            hosts = list(network.hosts())
            if hosts:
                self.append_output(f"  Usable Range: {hosts[0]} - {hosts[-1]}")
            self.append_output(f"  Network Address: {network.network_address}")
            self.append_output(f"  Broadcast Address: {network.broadcast_address}")
    
    def _display_subnet_masks(self, network):
        """Display subnet mask information."""
        self.append_output("\n--- Subnet Mask ---", 'INFO')
        self.append_output(f"  Dotted Decimal: {network.netmask}")
        
        # Binary representation
        binary = ''.join(f'{octet:08b}' for octet in network.network_address.packed)
        self.append_output(f"  Binary: {binary[:network.prefixlen]} (network) + {binary[network.prefixlen:]} (host)")
    
    def _display_hosts(self, network):
        """Display all hosts (for small networks)."""
        if network.num_addresses > 256:
            return
        
        self.append_output("\n--- All Host Addresses ---", 'INFO')
        
        hosts = list(network.hosts())
        if not hosts:
            self.append_output("  No usable hosts (point-to-point or single address)", 'WARNING')
        else:
            for i, host in enumerate(hosts[:50]):  # Limit to 50
                self.append_output(f"  Host {i+1}: {host}")
            
            if len(hosts) > 50:
                self.append_output(f"  ... and {len(hosts) - 50} more hosts")
    
    def _calculate_subnet_details(self, network):
        """Calculate and return subnet details."""
        details = {
            'network': str(network.network_address),
            'broadcast': str(network.broadcast_address) if network.broadcast_address else 'N/A',
            'netmask': str(network.netmask),
            'cidr': network.prefixlen,
            'total': network.num_addresses,
            'usable': max(0, network.num_addresses - 2),
            'first_usable': str(list(network.hosts())[0]) if network.num_addresses > 2 else 'N/A',
            'last_usable': str(list(network.hosts())[-1]) if network.num_addresses > 2 else 'N/A'
        }
        
        return details
