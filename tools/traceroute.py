"""
Traceroute Tool for NetSuite GUI
Traces the network path to a destination.
"""

import subprocess
import re
from tkinter import ttk
from .base_tool import BaseTool


class TracerouteTool(BaseTool):
    """Traceroute tool using Windows tracert command."""
    
    def create_ui(self, parent):
        """Create the traceroute UI."""
        # Input frame
        input_frame = ttk.LabelFrame(parent, text="Traceroute")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Destination input
        ttk.Label(input_frame, text="Destination:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.dest_var = ttk.StringVar(value="google.com")
        ttk.Entry(input_frame, textvariable=self.dest_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Max hops
        ttk.Label(input_frame, text="Max Hops:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.max_hops_var = ttk.StringVar(value="30")
        ttk.Entry(input_frame, textvariable=self.max_hops_var, width=8).grid(row=0, column=3, padx=5, pady=5)
        
        # Resolve hostnames
        self.resolve_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(input_frame, text="Resolve Hostnames", variable=self.resolve_var).grid(row=0, column=4, padx=5, pady=5)
        
        # Don't fragment
        self.dont_fragment_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(input_frame, text="Don't Fragment", variable=self.dont_fragment_var).grid(row=0, column=5, padx=5, pady=5)
        
        # Trace button
        self.trace_btn = ttk.Button(input_frame, text="Trace", command=self.run_tool)
        self.trace_btn.grid(row=0, column=6, padx=5, pady=5)
        
        # Output area
        self.create_output_area(parent)
    
    def run_tool(self):
        """Start traceroute."""
        dest = self.dest_var.get().strip()
        
        if not dest:
            self.append_output("Please enter a destination host or IP.", 'ERROR')
            return
        
        try:
            max_hops = int(self.max_hops_var.get())
            if max_hops < 1 or max_hops > 100:
                raise ValueError()
        except ValueError:
            self.append_output("Max hops must be between 1 and 100.", 'ERROR')
            return
        
        self.clear_output()
        self.print_header(f"Traceroute: {dest}")
        self.append_output(f"Tracing route to {dest} (max {max_hops} hops)...", 'INFO')
        self.append_output("-" * 60, 'INFO')
        
        # Update button state
        self.trace_btn.config(state=tk.DISABLED)
        
        # Start trace in thread
        self.run_in_thread(self._trace_thread, args=(dest, max_hops))
    
    def _trace_thread(self, dest, max_hops):
        """Traceroute thread."""
        try:
            self.gui.start_progress()
            self.gui.set_status(f"Tracing route to {dest}...")
            
            # Build tracert command
            cmd = ['tracert']
            
            if not self.resolve_var.get():
                cmd.append('-d')
            
            if self.dont_fragment_var.get():
                cmd.append('-f')
            
            cmd.extend(['-h', str(max_hops), dest])
            
            # Run tracert
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Stream output
            hop_count = 0
            for line in iter(process.stdout.readline, ''):
                if self.stop_event.is_set():
                    process.terminate()
                    self.append_output("\nTrace cancelled by user.", 'WARNING')
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Format and display output
                if line.startswith('Tracing route'):
                    continue
                elif 'unable to resolve' in line.lower():
                    self.append_output(f"  {line}", 'WARNING')
                elif 'Request timed out' in line:
                    hop_count += 1
                    self.append_output(f"  Hop {hop_count}: * * * Request timed out", 'WARNING')
                elif re.match(r'^\d+\s+', line):
                    hop_count += 1
                    self._format_hop_line(hop_count, line)
                else:
                    self.append_output(f"  {line}")
            
            process.wait()
            
            if not self.stop_event.is_set():
                self.append_output("\n" + "=" * 60, 'INFO')
                self.append_output("Trace complete!", 'SUCCESS')
                self.append_output("=" * 60, 'INFO')
        
        except Exception as e:
            self.append_output(f"Error during trace: {e}", 'ERROR')
        finally:
            self.trace_btn.config(state=tk.NORMAL)
            self.gui.stop_progress()
            self.gui.set_status("Ready")
    
    def _format_hop_line(self, hop_num, line):
        """Format a traceroute hop line for display."""
        # Parse hop information
        # Example: "1   <1 ms    <1 ms    <1 ms  192.168.1.1"
        
        parts = line.split()
        
        if len(parts) < 2:
            self.append_output(f"  Hop {hop_num}: {line}", 'WARNING')
            return
        
        # Try to extract IP addresses and times
        times = []
        ips = []
        
        for i, part in enumerate(parts[1:], 1):
            if 'ms' in part:
                try:
                    times.append(part)
                except:
                    pass
            elif self._is_ip(part):
                ips.append(part)
        
        # Format output
        if ips:
            ip = ips[0]
            time_str = ' | '.join(times[-3:]) if times else 'Timeout'
            self.append_output(f"  Hop {hop_num}: {ip} ({time_str})", 'SUCCESS')
        else:
            self.append_output(f"  Hop {hop_num}: {line}", 'INFO')
    
    def _is_ip(self, s):
        """Check if string is an IP address."""
        # Simple IP check
        parts = s.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except:
            return False
