"""Client module for sending commands to server."""
import socket
import sys
import threading
import platform

# Platform-specific imports
if platform.system() != 'Windows':
    import termios
    import tty
else:
    termios = None
    tty = None


class CommandClient:
    """Client that sends keyboard commands to the server."""
    
    PORT = 5001
    
    def __init__(self, server_ip, status_callback=None, use_gui=False):
        self.server_ip = server_ip
        self.status_callback = status_callback
        self.running = False
        self.socket = None
        self.old_settings = None
        self.use_gui = use_gui
        self.pending_chars = []
        self.char_lock = threading.Lock()
    
    def _update_status(self, message):
        """Update status via callback if available."""
        if self.status_callback:
            self.status_callback(f"Client: {message}")
    
    def send_char(self, char):
        """Send a character to the server (for GUI mode)."""
        if self.socket and self.running:
            try:
                self.socket.send(char.encode())
                if ord(char) == 3:  # Ctrl+C
                    self._update_status("Disconnecting...")
                    self.stop()
            except Exception as e:
                self._update_status(f"Error sending char: {e}")
    
    def _run_terminal_mode(self):
        """Run client in terminal mode (original behavior - Unix only)."""
        if platform.system() == 'Windows':
            self._update_status("Terminal mode is not supported on Windows. Please use GUI mode.")
            self.running = False
            return
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.PORT))
            self._update_status(f"Connected to {self.server_ip}:{self.PORT}")
            self._update_status("Press keys (Ctrl+C to exit)")
            
            # Save terminal settings (Unix only)
            if termios:
                self.old_settings = termios.tcgetattr(sys.stdin)
                
                # Set terminal to raw mode
                if tty:
                    tty.setraw(sys.stdin.fileno())
            
            while self.running:
                char = sys.stdin.read(1)
                self.socket.send(char.encode())
                if ord(char) == 3:  # Ctrl+C
                    self._update_status("Disconnecting...")
                    break
                    
        except ConnectionRefusedError:
            self._update_status(f"Connection refused. Is server running at {self.server_ip}?")
        except Exception as e:
            self._update_status(f"Error: {e}")
        finally:
            self._cleanup_terminal()
            self.stop()
    
    def _run_gui_mode(self):
        """Run client in GUI mode (just establish connection)."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.PORT))
            self._update_status(f"Connected to {self.server_ip}:{self.PORT}")
            self._update_status("Ready to send commands. Use keyboard input in GUI.")
        except ConnectionRefusedError:
            self._update_status(f"Connection refused. Is server running at {self.server_ip}?")
            self.running = False
        except Exception as e:
            self._update_status(f"Error: {e}")
            self.running = False
    
    def _cleanup_terminal(self):
        """Restore terminal settings (Unix only)."""
        if self.old_settings and termios:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except:
                pass
    
    def start(self):
        """Start the client."""
        self.running = True
        
        if self.use_gui:
            self._run_gui_mode()
        else:
            self._run_terminal_mode()
    
    def stop(self):
        """Stop the client."""
        self.running = False
        self._cleanup_terminal()
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self._update_status("Client stopped")

