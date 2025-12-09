"""Main GUI application for server and client modes."""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from utils import get_local_ip
from server_modules import GamepadServer, StreamServer
from client_modules import CommandClient


class Application:
    """Main application class."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gamepad Control System")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Server components
        self.gamepad_server = None
        self.stream_server = None
        self.gamepad_thread = None
        self.stream_thread = None
        self.server_running = False
        
        # Client components
        self.client = None
        self.client_thread = None
        self.client_running = False
        self.client_input_window = None
        
        # Local IP
        self.local_ip = get_local_ip()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create GUI widgets."""
        # Mode selection
        mode_frame = ttk.LabelFrame(self.root, text="Mode Selection", padding=10)
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.mode_var = tk.StringVar(value="server")
        
        ttk.Radiobutton(
            mode_frame, 
            text="Server Mode", 
            variable=self.mode_var, 
            value="server",
            command=self._switch_mode
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            mode_frame, 
            text="Client Mode", 
            variable=self.mode_var, 
            value="client",
            command=self._switch_mode
        ).pack(side=tk.LEFT, padx=5)
        
        # Server mode frame
        self.server_frame = ttk.LabelFrame(self.root, text="Server Mode", padding=10)
        self.server_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # IP display for server
        ip_frame = ttk.Frame(self.server_frame)
        ip_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ip_frame, text="Server IP Address:").pack(side=tk.LEFT)
        self.server_ip_label = ttk.Label(ip_frame, text="Not started", font=("Arial", 10, "bold"))
        self.server_ip_label.pack(side=tk.LEFT, padx=10)
        
        # Status display for server
        ttk.Label(self.server_frame, text="Status:").pack(anchor=tk.W, pady=(10, 5))
        self.server_status = scrolledtext.ScrolledText(
            self.server_frame, 
            height=8, 
            width=60,
            state=tk.DISABLED
        )
        self.server_status.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Server buttons
        server_btn_frame = ttk.Frame(self.server_frame)
        server_btn_frame.pack(fill=tk.X, pady=5)
        
        self.server_start_btn = ttk.Button(
            server_btn_frame, 
            text="Start Server", 
            command=self._start_server
        )
        self.server_start_btn.pack(side=tk.LEFT, padx=5)
        
        self.server_stop_btn = ttk.Button(
            server_btn_frame, 
            text="Stop Server", 
            command=self._stop_server,
            state=tk.DISABLED
        )
        self.server_stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Client mode frame
        self.client_frame = ttk.LabelFrame(self.root, text="Client Mode", padding=10)
        
        # IP input for client
        ip_input_frame = ttk.Frame(self.client_frame)
        ip_input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ip_input_frame, text="Server IP:").pack(side=tk.LEFT)
        self.client_ip_entry = ttk.Entry(ip_input_frame, width=20)
        self.client_ip_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Display IP for client
        display_frame = ttk.Frame(self.client_frame)
        display_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(display_frame, text="Connected to:").pack(side=tk.LEFT)
        self.client_ip_display = ttk.Label(display_frame, text="Not connected", font=("Arial", 10, "bold"))
        self.client_ip_display.pack(side=tk.LEFT, padx=10)
        
        # Status display for client
        ttk.Label(self.client_frame, text="Status:").pack(anchor=tk.W, pady=(10, 5))
        self.client_status = scrolledtext.ScrolledText(
            self.client_frame, 
            height=8, 
            width=60,
            state=tk.DISABLED
        )
        self.client_status.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Client buttons
        client_btn_frame = ttk.Frame(self.client_frame)
        client_btn_frame.pack(fill=tk.X, pady=5)
        
        self.client_start_btn = ttk.Button(
            client_btn_frame, 
            text="Connect & Start", 
            command=self._start_client
        )
        self.client_start_btn.pack(side=tk.LEFT, padx=5)
        
        self.client_stop_btn = ttk.Button(
            client_btn_frame, 
            text="Stop Client", 
            command=self._stop_client,
            state=tk.DISABLED
        )
        self.client_stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Instructions for client
        ttk.Label(
            self.client_frame, 
            text="After connecting, a keyboard input window will open. Type commands there.",
            font=("Arial", 9),
            foreground="gray"
        ).pack(pady=5)
        
        # Initially show server mode
        self._switch_mode()
    
    def _switch_mode(self):
        """Switch between server and client modes."""
        mode = self.mode_var.get()
        
        if mode == "server":
            self.client_frame.pack_forget()
            self.server_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        else:
            self.server_frame.pack_forget()
            self.client_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def _log_server_status(self, message):
        """Log message to server status text area."""
        self.server_status.config(state=tk.NORMAL)
        self.server_status.insert(tk.END, message + "\n")
        self.server_status.see(tk.END)
        self.server_status.config(state=tk.DISABLED)
    
    def _log_client_status(self, message):
        """Log message to client status text area."""
        self.client_status.config(state=tk.NORMAL)
        self.client_status.insert(tk.END, message + "\n")
        self.client_status.see(tk.END)
        self.client_status.config(state=tk.DISABLED)
    
    def _start_server(self):
        """Start both gamepad and stream servers."""
        if self.server_running:
            return
        
        self.server_running = True
        self.server_start_btn.config(state=tk.DISABLED)
        self.server_stop_btn.config(state=tk.NORMAL)
        
        # Clear status
        self.server_status.config(state=tk.NORMAL)
        self.server_status.delete(1.0, tk.END)
        self.server_status.config(state=tk.DISABLED)
        
        # Update IP display
        self.local_ip = get_local_ip()
        self.server_ip_label.config(text=self.local_ip)
        
        # Create servers with status callbacks
        self.gamepad_server = GamepadServer(status_callback=self._log_server_status)
        self.stream_server = StreamServer(status_callback=self._log_server_status)
        
        # Start stream server in a thread
        self.stream_server.start()
        self._log_server_status("Stream server starting...")
        
        # Start gamepad server in a thread
        self.gamepad_thread = threading.Thread(target=self.gamepad_server.start, daemon=True)
        self.gamepad_thread.start()
        
        self._log_server_status("Gamepad server starting...")
        self._log_server_status(f"Both servers are running!")
        self._log_server_status(f"Server IP: {self.local_ip}")
        self._log_server_status(f"Stream available at: http://{self.local_ip}:8000")
        self._log_server_status(f"Gamepad server listening on port 5001")
    
    def _stop_server(self):
        """Stop both servers."""
        if not self.server_running:
            return
        
        self.server_running = False
        
        if self.gamepad_server:
            self.gamepad_server.stop()
        if self.stream_server:
            self.stream_server.stop()
        
        self.server_start_btn.config(state=tk.NORMAL)
        self.server_stop_btn.config(state=tk.DISABLED)
        self.server_ip_label.config(text="Not started")
        self._log_server_status("Servers stopped.")
    
    def _start_client(self):
        """Start the client."""
        if self.client_running:
            return
        
        server_ip = self.client_ip_entry.get().strip()
        if not server_ip:
            messagebox.showerror("Error", "Please enter a server IP address")
            return
        
        self.client_running = True
        self.client_start_btn.config(state=tk.DISABLED)
        self.client_stop_btn.config(state=tk.NORMAL)
        
        # Clear status
        self.client_status.config(state=tk.NORMAL)
        self.client_status.delete(1.0, tk.END)
        self.client_status.config(state=tk.DISABLED)
        
        # Update IP display
        self.client_ip_display.config(text=server_ip)
        
        # Create and start client in GUI mode
        self.client = CommandClient(server_ip, status_callback=self._log_client_status, use_gui=True)
        self.client_thread = threading.Thread(target=self.client.start, daemon=True)
        self.client_thread.start()
        
        # Wait a bit for connection, then open input window
        self.root.after(500, self._open_client_input_window)
    
    def _open_client_input_window(self):
        """Open a window for keyboard input."""
        if not self.client_running or not self.client or not self.client.socket:
            return
        
        # Create input window
        self.client_input_window = tk.Toplevel(self.root)
        self.client_input_window.title("Command Input - Press keys to send commands")
        self.client_input_window.geometry("400x200")
        
        # Instructions
        ttk.Label(
            self.client_input_window,
            text="This window captures keyboard input.\nClick here and type commands.",
            font=("Arial", 10),
            justify=tk.CENTER
        ).pack(pady=20)
        
        # Input field (for display, but we'll capture all keys)
        self.client_input_field = tk.Text(
            self.client_input_window,
            height=5,
            width=40,
            wrap=tk.WORD
        )
        self.client_input_field.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.client_input_field.focus_set()
        
        # Bind keyboard events
        self.client_input_window.bind("<KeyPress>", self._on_client_key_press)
        self.client_input_field.bind("<KeyPress>", self._on_client_key_press)
        
        # Handle window close
        self.client_input_window.protocol("WM_DELETE_WINDOW", self._close_client_input_window)
        
        self._log_client_status("Keyboard input window opened. Start typing commands.")
    
    def _on_client_key_press(self, event):
        """Handle key press in client input window."""
        if not self.client or not self.client_running:
            return
        
        char = None
        
        # Handle arrow keys (escape sequences)
        if event.keysym == "Up":
            # Send escape sequence: ESC [ A
            self.client.send_char("\x1b")
            self.client.send_char("[")
            self.client.send_char("A")
            return "break"
        elif event.keysym == "Down":
            self.client.send_char("\x1b")
            self.client.send_char("[")
            self.client.send_char("B")
            return "break"
        elif event.keysym == "Right":
            self.client.send_char("\x1b")
            self.client.send_char("[")
            self.client.send_char("C")
            return "break"
        elif event.keysym == "Left":
            self.client.send_char("\x1b")
            self.client.send_char("[")
            self.client.send_char("D")
            return "break"
        # Handle other special keys
        elif event.keysym == "Return":
            char = "\n"
        elif event.keysym == "BackSpace":
            char = "\b"
        elif event.keysym == "Tab":
            char = "\t"
        elif event.keysym == "Escape":
            char = "\x1b"
        elif event.keysym == "space":
            char = " "
        # Handle control combinations
        elif event.state & 0x4:  # Control key pressed
            if event.keysym.lower() == "c":
                char = "\x03"  # Ctrl+C
            elif event.keysym.lower() == "d":
                char = "\x04"  # Ctrl+D
            else:
                # For other Ctrl combinations, try to get the character
                char = event.char if event.char else None
        else:
            # Regular character
            char = event.char if event.char else None
        
        # Send the character if we have one
        if char:
            self.client.send_char(char)
        
        # Don't insert the character in the text field
        return "break"
    
    def _close_client_input_window(self):
        """Close the client input window."""
        if self.client_input_window:
            self.client_input_window.destroy()
            self.client_input_window = None
        self._stop_client()
    
    def _stop_client(self):
        """Stop the client."""
        if not self.client_running:
            return
        
        self.client_running = False
        
        # Close input window
        if self.client_input_window:
            self.client_input_window.destroy()
            self.client_input_window = None
        
        if self.client:
            self.client.stop()
        
        self.client_start_btn.config(state=tk.NORMAL)
        self.client_stop_btn.config(state=tk.DISABLED)
        self.client_ip_display.config(text="Not connected")
        self._log_client_status("Client stopped.")
    
    def on_closing(self):
        """Handle window closing."""
        if self.server_running:
            self._stop_server()
        if self.client_running:
            self._stop_client()
        if self.client_input_window:
            self.client_input_window.destroy()
        self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = Application(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

