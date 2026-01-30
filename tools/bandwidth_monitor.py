"""
Bandwidth Monitor Tool for NetSuite GUI
Monitors network interface bandwidth usage.
"""

import subprocess
import re
import time
from tkinter import ttk
from .base_tool import BaseTool


class BandwidthMonitorTool(BaseTool):
    """Network bandwidth monitoring tool."""
    
    def create_ui(self, parent):
        """Create the bandwidth monitor UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Bandwidth Monitor")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Interface selector
        ttk.Label(input_frame, text="Interface:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.interface_var = ttk.StringVar(value="auto")
        self.interface_combo = ttk.Combobox(input_frame, textvariable=self.interface_var, 
                                           width=20, state="readonly")
        self.interface_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Refresh button
        ttk.Button(input_frame, text="Refresh Interfaces", 
                  command=self.refresh_interfaces).grid(row=0, column=2, padx=5, pady=5)
        
        # Update interval
        ttk.Label(input_frame, text="Interval (s):").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.interval_var = ttk.StringVar(value="2")
        ttk.Entry(input_frame, textvariable=self.interval_var, width=5).grid(row=0, column=4, padx=5, pady=5)
        
        # Start/Stop button
        self.monitor_btn = ttk.Button(input_frame, text="Start Monitor", command=self.toggle_monitor)
        self.monitor_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
        
        # Refresh interfaces on startup
        self.refresh_interfaces()
    
    def refresh_interfaces(self):
        """Refresh list of network interfaces."""
        interfaces = ['auto']
        
        try:
            result = subprocess.run(
                ['netstat', '-e'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse interfaces
            lines = result.stdout.split('\n')
            for line in lines:
                if 'bytes' in line.lower() and not line.startswith('  '):
                    parts = line.split()
                    if parts:
                        interface = parts[0]
                        if interface not in interfaces:
                            interfaces.append(interface)
        
        except Exception as e:
            self.append_output(f"Error getting interfaces: {e}", 'ERROR')
        
        self.interface_combo['values'] = interfaces
        if interfaces:
            self.interface_combo.current(0)
    
    def toggle_monitor(self):
        """Toggle bandwidth monitoring."""
        if self.is_running():
            self.stop_monitor()
        else:
            self.start_monitor()
    
    def start_monitor(self):
        """Start bandwidth monitoring."""
        self.clear_output()
        self.print_header("Bandwidth Monitor")
        
        try:
            interval = float(self.interval_var.get())
            if interval < 0.5 or interval > 60:
                raise ValueError()
        except ValueError:
            self.append_output("Invalid interval. Use 0.5-60 seconds.", 'ERROR')
            return
        
        self.monitor_btn.config(text="Stop Monitor")
        self.run_in_thread(self._monitor_bandwidth, args=(interval,))
    
    def stop_monitor(self):
        """Stop bandwidth monitoring."""
        self.stop_event.set()
        self.monitor_btn.config(text="Start Monitor")
        self.gui.set_status("Stopping monitor...")
    
    def _monitor_bandwidth(self, interval):
        """Monitor bandwidth usage."""
        try:
            self.gui.start_progress()
            
            interface = self.interface_var.get()
            
            self.append_output(f"\nMonitoring bandwidth usage (update every {interval}s)", 'INFO')
            self.append_output("Press 'Stop Monitor' to stop.", 'INFO')
            self.append_output("-" * 70, 'INFO')
            
            # Get initial stats
            prev_stats = self._get_interface_stats(interface)
            prev_time = time.time()
            
            iteration = 0
            
            while not self.stop_event.is_set():
                iteration += 1
                
                # Wait for interval
                time.sleep(interval)
                
                if self.stop_event.is_set():
                    break
                
                # Get current stats
                curr_stats = self._get_interface_stats(interface)
                curr_time = time.time()
                
                # Calculate rates
                time_diff = curr_time - prev_time
                
                self.append_output(f"\n--- Update {iteration} ---", 'INFO')
                
                for iface, stats in curr_stats.items():
                    if iface in prev_stats:
                        prev = prev_stats[iface]
                        
                        # Calculate differences
                        bytes_sent_diff = stats['bytes_sent'] - prev['bytes_sent']
                        bytes_recv_diff = stats['bytes_recv'] - prev['bytes_recv']
                        
                        # Calculate rates (bytes per second)
                        send_rate = bytes_sent_diff / time_diff if time_diff > 0 else 0
                        recv_rate = bytes_recv_diff / time_diff if time_diff > 0 else 0
                        
                        # Format for display
                        self.append_output(f"\n{iface}:", 'INFO')
                        self.append_output(f"  ↓ Download: {self._format_speed(recv_rate)}", 'SUCCESS')
                        self.append_output(f"  ↑ Upload:   {self._format_speed(send_rate)}", 'SUCCESS')
                        self.append_output(f"  Total Sent: {self._format_bytes(stats['bytes_sent'])}")
                        self.append_output(f"  Total Recv: {self._format_bytes(stats['bytes_recv'])}")
                
                prev_stats = curr_stats
                prev_time = curr_time
            
            self.append_output("\n" + "=" * 70, 'INFO')
            self.append_output("Monitoring stopped.", 'INFO')
        
        except Exception as e:
            self.append_output(f"\nError monitoring bandwidth: {e}", 'ERROR')
        finally:
            self.monitor_btn.config(text="Start Monitor")
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _get_interface_stats(self, interface):
        """Get interface statistics."""
        stats = {}
        
        try:
            result = subprocess.run(
                ['netstat', '-e'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.split('\n')
            
            current_interface = None
            for line in lines:
                if 'bytes' in line.lower():
                    parts = line.split()
                    if parts and not line.startswith('  '):
                        # Interface name
                        current_interface = parts[0]
                        
                        # Skip if filtering and not matching
                        if interface != 'auto' and interface != current_interface:
                            current_interface = None
                            continue
                    
                    # Parse stats
                    if current_interface and len(parts) >= 3:
                        try:
                            bytes_sent = int(parts[1].replace(',', ''))
                            bytes_recv = int(parts[2].replace(',', ''))
                            
                            stats[current_interface] = {
                                'bytes_sent': bytes_sent,
                                'bytes_recv': bytes_recv
                            }
                        except (ValueError, IndexError):
                            pass
        
        except Exception as e:
            pass
        
        return stats
    
    def _format_speed(self, bytes_per_sec):
        """Format bandwidth speed for display."""
        if bytes_per_sec >= 1_000_000:
            return f"{bytes_per_sec / 1_000_000:.2f} MB/s"
        elif bytes_per_sec >= 1_000:
            return f"{bytes_per_sec / 1_000:.2f} KB/s"
        else:
            return f"{bytes_per_sec:.0f} B/s"
    
    def _format_bytes(self, bytes_total):
        """Format byte count for display."""
        if bytes_total >= 1_000_000_000:
            return f"{bytes_total / 1_000_000_000:.2f} GB"
        elif bytes_total >= 1_000_000:
            return f"{bytes_total / 1_000_000:.2f} MB"
        elif bytes_total >= 1_000:
            return f"{bytes_total / 1_000:.2f} KB"
        else:
            return f"{bytes_total} B"
