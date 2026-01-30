"""
Ping Tool for NetSuite GUI
Performs ICMP ping with statistics and continuous monitoring.
"""

import subprocess
import re
import time
import tkinter as tk
from tkinter import ttk
from .base_tool import BaseTool


class PingTool(BaseTool):
    """Ping tool with continuous monitoring and statistics."""
    
    def create_ui(self, parent):
        """Create the ping UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Ping")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Host input
        ttk.Label(input_frame, text="Host/IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.host_var = ttk.StringVar(value="8.8.8.8")
        ttk.Entry(input_frame, textvariable=self.host_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Ping count
        ttk.Label(input_frame, text="Count:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.count_var = ttk.StringVar(value="4")
        ttk.Entry(input_frame, textvariable=self.count_var, width=8).grid(row=0, column=3, padx=5, pady=5)
        
        # Continuous ping
        self.continuous_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(input_frame, text="Continuous", variable=self.continuous_var).grid(row=0, column=4, padx=5, pady=5)
        
        # Ping button
        self.ping_btn = ttk.Button(input_frame, text="Ping", command=self.run_tool)
        self.ping_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # Stop button (hidden initially)
        self.stop_btn = ttk.Button(input_frame, text="Stop", command=self.stop_ping, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=6, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Start ping."""
        host = self.host_var.get().strip()
        
        if not host:
            self.append_output("Please enter a host or IP address.", 'ERROR')
            return
        
        self.clear_output()
        self.print_header(f"Ping: {host}")
        
        # Update button states
        self.ping_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start ping in thread
        self.run_in_thread(self._ping_thread, args=(host,))
    
    def _ping_thread(self, host):
        """Ping thread."""
        try:
            continuous = self.continuous_var.get()
            count = self.count_var.get() if not continuous else None
            
            if continuous:
                self._ping_continuous(host)
            else:
                self._ping_count(host, count)
        
        except Exception as e:
            self.append_output(f"Error: {e}", 'ERROR')
        finally:
            self.ping_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.gui.stop_progress()
    
    def _ping_count(self, host, count):
        """Ping with specified count."""
        try:
            count = int(count)
            if count < 1 or count > 1000:
                raise ValueError("Count must be between 1 and 1000")
        except ValueError as e:
            self.append_output(f"Invalid count: {e}", 'ERROR')
            return
        
        self.gui.start_progress()
        self.gui.set_status(f"Pinging {host}...")
        
        # Build ping command for Windows
        cmd = ['ping', '-n', str(count), host]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Stream output
            for line in iter(process.stdout.readline, ''):
                if self.stop_event.is_set():
                    process.terminate()
                    break
                
                line = line.strip()
                if line:
                    # Color code the output
                    if 'Reply from' in line or 'bytes=' in line:
                        self.append_output(line, 'SUCCESS')
                    elif 'Request timed out' in line or 'Destination host unreachable' in line:
                        self.append_output(line, 'ERROR')
                    elif 'Packet:' in line or 'Packets:' in line or 'Minimum' in line:
                        self.append_output(line, 'INFO')
                    else:
                        self.append_output(line)
            
            process.wait()
            
            # Parse statistics
            self._parse_ping_stats(host, count)
            
        except Exception as e:
            self.append_output(f"Error executing ping: {e}", 'ERROR')
    
    def _ping_continuous(self, host):
        """Continuous ping with statistics."""
        self.gui.start_progress()
        self.gui.set_status(f"Pinging {host} continuously...")
        
        self.append_output("Continuous ping started. Press 'Stop' to end.", 'INFO')
        self.append_output("-" * 50, 'INFO')
        
        sent = 0
        received = 0
        times = []
        
        # Build ping command
        cmd = ['ping', '-t', host]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            for line in iter(process.stdout.readline, ''):
                if self.stop_event.is_set():
                    process.terminate()
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                sent += 1
                
                # Parse ping response
                if 'Reply from' in line and 'time=' in line:
                    received += 1
                    self.append_output(line, 'SUCCESS')
                    
                    # Extract time
                    match = re.search(r'time[=<](\d+)ms', line)
                    if match:
                        times.append(int(match.group(1)))
                
                elif 'Request timed out' in line:
                    self.append_output(line, 'ERROR')
                
                # Update statistics every 10 pings
                if sent % 10 == 0 and sent > 0:
                    self._print_inline_stats(sent, received, times)
            
            # Final statistics
            self.append_output("\n" + "=" * 50, 'INFO')
            self._print_inline_stats(sent, received, times, final=True)
            
        except Exception as e:
            self.append_output(f"Error: {e}", 'ERROR')
    
    def _print_inline_stats(self, sent, received, times, final=False):
        """Print inline statistics."""
        if sent == 0:
            return
        
        loss = ((sent - received) / sent) * 100
        
        if times:
            avg = sum(times) / len(times)
            min_t = min(times)
            max_t = max(times)
            
            stats = f"Stats: {sent} sent, {received} received, {loss:.0f}% loss | " \
                    f"RTT: min={min_t}ms, max={max_t}ms, avg={avg:.1f}ms"
        else:
            stats = f"Stats: {sent} sent, {received} received, {loss:.0f}% loss"
        
        if final:
            self.append_output(stats, 'INFO')
        else:
            # Print on same line (simulate with overwriting)
            pass
    
    def _parse_ping_stats(self, host, count):
        """Parse and display ping statistics."""
        self.append_output("\n" + "=" * 50, 'INFO')
        self.append_output("Ping Statistics Summary", 'INFO')
        self.append_output("=" * 50, 'INFO')
        
        # Run a quick ping to get stats
        cmd = ['ping', '-n', str(count), host]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = result.stdout + result.stderr
            
            # Parse Windows ping statistics
            lines = output.split('\n')
            
            for line in lines:
                line = line.strip()
                if 'Packets:' in line or 'Packet:' in line:
                    self.append_output(f"  {line}", 'INFO')
                elif 'Minimum' in line or 'Maximum' in line or 'Average' in line:
                    self.append_output(f"  {line}", 'INFO')
        
        except Exception:
            pass
    
    def stop_ping(self):
        """Stop continuous ping."""
        self.stop_event.set()
        self.gui.set_status("Stopping ping...")
