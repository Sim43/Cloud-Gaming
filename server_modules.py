"""Server modules for gamepad control and streaming."""
import socket
import time
import vgamepad as vg
import io
import mss
import threading
from PIL import Image
from flask import Flask, Response


class GamepadServer:
    """Server that receives commands and converts them to virtual gamepad inputs."""
    
    HOST = "0.0.0.0"
    PORT = 5001
    
    # Arrow escape sequences from Linux terminal
    ESC_MAP = {
        "\x1b[A": "up",
        "\x1b[B": "down",
        "\x1b[C": "right",
        "\x1b[D": "left",
    }
    
    # Character to gamepad mapping
    CHAR_MAP = {
        "w": ("dpad", "up"),
        "s": ("dpad", "down"),
        "a": ("dpad", "left"),
        "d": ("dpad", "right"),
        "u": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
        "i": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
        "j": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
        "k": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
        " ": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
    }
    
    DPAD_MAP = {
        "up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        "down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
        "left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        "right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    }
    
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.running = False
        self.socket = None
        self.conn = None
        self.gamepad = None
        self.esc_buf = ""
        
    def _update_status(self, message):
        """Update status via callback if available."""
        if self.status_callback:
            self.status_callback(f"Gamepad Server: {message}")
    
    def press_gamepad_action(self, kind, value, duration=0.05):
        """Press a gamepad button/dpad briefly."""
        try:
            if kind == "button":
                self.gamepad.press_button(button=value)
                self.gamepad.update()
                time.sleep(duration)
                self.gamepad.release_button(button=value)
                self.gamepad.update()
            elif kind == "dpad":
                btn = self.DPAD_MAP[value]
                self.gamepad.press_button(button=btn)
                self.gamepad.update()
                time.sleep(duration)
                self.gamepad.release_button(button=btn)
                self.gamepad.update()
        except Exception as e:
            self._update_status(f"Error sending gamepad action {kind} {value}: {e}")
    
    def start(self):
        """Start the gamepad server."""
        self.running = True
        self.gamepad = vg.VX360Gamepad()
        self.esc_buf = ""
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.HOST, self.PORT))
        self.socket.listen(1)
        
        self._update_status(f"Listening on {self.HOST}:{self.PORT}...")
        
        try:
            self.conn, addr = self.socket.accept()
            self._update_status(f"Client connected: {addr}")
            
            while self.running:
                data = self.conn.recv(1024)
                if not data:
                    self._update_status("Client disconnected")
                    break
                
                for b in data:
                    ch = chr(b)
                    
                    # Ctrl+C from client -> exit server
                    if b == 3:
                        self._update_status("Received Ctrl+C, shutting down server.")
                        self.running = False
                        break
                    
                    # Handle escape sequences
                    if self.esc_buf:
                        self.esc_buf += ch
                        if self.esc_buf in self.ESC_MAP:
                            direction = self.ESC_MAP[self.esc_buf]
                            self.press_gamepad_action("dpad", direction)
                            self.esc_buf = ""
                            continue
                        if not any(seq.startswith(self.esc_buf) for seq in self.ESC_MAP):
                            self.esc_buf = ""
                        continue
                    
                    # Start of escape sequence
                    if ch == "\x1b":
                        self.esc_buf = ch
                        continue
                    
                    # Ignore newlines/carriage returns
                    if ch in ("\n", "\r"):
                        continue
                    
                    # Normal mapped keys
                    if ch in self.CHAR_MAP:
                        kind, value = self.CHAR_MAP[ch]
                        self.press_gamepad_action(kind, value)
        except Exception as e:
            self._update_status(f"Error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the gamepad server."""
        self.running = False
        if self.conn:
            self.conn.close()
        if self.socket:
            self.socket.close()
        self._update_status("Gamepad server stopped")


class StreamServer:
    """Server that streams screen captures via Flask."""
    
    PORT = 8000
    
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.app = Flask(__name__)
        self.running = False
        self.thread = None
        self._thread_local = threading.local()
        self._setup_routes()
    
    def _update_status(self, message):
        """Update status via callback if available."""
        if self.status_callback:
            self.status_callback(f"Stream Server: {message}")
    
    def get_sct(self):
        """Get or create thread-local mss instance."""
        if not hasattr(self._thread_local, 'sct'):
            self._thread_local.sct = mss.mss()
        return self._thread_local.sct
    
    def generate_frames(self):
        """Generate video frames from screen capture."""
        sct = self.get_sct()
        monitor = sct.monitors[1]  # usually main screen
        
        while self.running:
            try:
                shot = sct.grab(monitor)
                img = Image.frombytes('RGB', shot.size, shot.rgb)
                
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=60)
                jpg_bytes = buf.getvalue()
                
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpg_bytes + b'\r\n'
                )
            except Exception as e:
                self._update_status(f"Frame generation error: {e}")
                break
    
    def _setup_routes(self):
        """Setup Flask routes."""
        @self.app.route('/stream')
        def stream():
            return Response(
                self.generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        
        @self.app.route('/')
        def index():
            return """
            <html>
              <body style="margin:0;background:black;display:flex;justify-content:center;align-items:center;height:100vh;">
                <img src="/stream" style="max-width:100%;max-height:100%;" />
              </body>
            </html>
            """
    
    def _run_flask(self):
        """Run Flask server in a thread."""
        try:
            self._update_status(f"Starting stream server on port {self.PORT}...")
            self.app.run(host="0.0.0.0", port=self.PORT, threaded=False, use_reloader=False)
        except Exception as e:
            self._update_status(f"Stream server error: {e}")
        finally:
            self.running = False
    
    def start(self):
        """Start the stream server in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_flask, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the stream server."""
        self.running = False
        self._update_status("Stream server stopped")

