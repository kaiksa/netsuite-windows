"""
Base Tool Class for NetSuite GUI
All tools inherit from this base class.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import queue
from datetime import datetime


class BaseTool:
    """Base class for all network tools."""
    
    def __init__(self, gui):
        self.gui = gui
        self.name = self.__class__.__name__
        self.output_widget = None
        self.worker_thread = None
        self.stop_event = threading.Event()
    
    def create_ui(self, parent):
        """Create the UI for this tool. Override in subclass."""
        raise NotImplementedError
    
    def run_tool(self):
        """Run the tool. Override in subclass."""
        raise NotImplementedError
    
    def create_output_area(self, parent):
        """Create a standard output text area."""
        # Output frame
        output_frame = ttk.LabelFrame(parent, text="Output")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text widget with scrollbar
        self.output_widget = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.output_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure tags for color coding
        self.output_widget.tag_config('INFO', foreground='blue')
        self.output_widget.tag_config('WARNING', foreground='orange')
        self.output_widget.tag_config('ERROR', foreground='red')
        self.output_widget.tag_config('SUCCESS', foreground='green')
        self.output_widget.tag_config('HEADER', foreground='purple', font=('Consolas', 9, 'bold'))
        self.output_widget.tag_config('TIMESTAMP', foreground='gray')
    
    def append_output(self, text, tag=None):
        """Append text to the output widget."""
        if self.output_widget:
            self.output_widget.config(state=tk.NORMAL)
            
            # Add timestamp if no tag specified
            if tag is None:
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.output_widget.insert(tk.END, f"[{timestamp}] ", 'TIMESTAMP')
                self.output_widget.insert(tk.END, text + '\n')
            else:
                self.output_widget.insert(tk.END, text + '\n', tag)
            
            self.output_widget.config(state=tk.DISABLED)
            self.output_widget.see(tk.END)
    
    def clear_output(self):
        """Clear the output widget."""
        if self.output_widget:
            self.output_widget.config(state=tk.NORMAL)
            self.output_widget.delete(1.0, tk.END)
            self.output_widget.config(state=tk.DISABLED)
    
    def export_results(self):
        """Export output to a file."""
        if not self.output_widget:
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            title=f"Export {self.name} Results"
        )
        
        if file_path:
            try:
                content = self.output_widget.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                from tkinter import messagebox
                messagebox.showinfo("Export Complete", f"Results exported to {file_path}")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def run_in_thread(self, target, args=(), kwargs=None):
        """Run a function in a separate thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            return False
        
        self.stop_event.clear()
        kwargs = kwargs or {}
        
        self.worker_thread = threading.Thread(
            target=target,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        self.worker_thread.start()
        return True
    
    def stop(self):
        """Stop the current operation."""
        self.stop_event.set()
    
    def is_running(self):
        """Check if a tool is currently running."""
        return self.worker_thread and self.worker_thread.is_alive()
    
    def print_header(self, title):
        """Print a formatted header."""
        self.append_output("=" * 60, 'HEADER')
        self.append_output(f"  {title}", 'HEADER')
        self.append_output("=" * 60, 'HEADER')
    
    def print_result(self, label, value, success=True):
        """Print a formatted result line."""
        tag = 'SUCCESS' if success else 'ERROR'
        self.append_output(f"{label}: {value}", tag)
