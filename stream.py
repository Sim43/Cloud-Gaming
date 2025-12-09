import io
import mss
import threading
from PIL import Image
from flask import Flask, Response

app = Flask(__name__)

# Thread-local storage for mss instance
_thread_local = threading.local()

def get_sct():
    """Get or create thread-local mss instance"""
    if not hasattr(_thread_local, 'sct'):
        _thread_local.sct = mss.mss()
    return _thread_local.sct

def generate_frames():
    sct = get_sct()
    monitor = sct.monitors[1]  # usually main screen
    
    while True:
        # Capture screen
        shot = sct.grab(monitor)

        # Create PIL image from raw data (RGB)
        img = Image.frombytes('RGB', shot.size, shot.rgb)

        # Optionally resize to reduce bandwidth / load
        # img = img.resize((1280, 720))

        # Encode to JPEG in memory
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=60)
        jpg_bytes = buf.getvalue()

        # MJPEG chunk
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + jpg_bytes + b'\r\n'
        )

@app.route('/stream')
def stream():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/')
def index():
    # Tiny page to embed the stream
    return """
    <html>
      <body style="margin:0;background:black;display:flex;justify-content:center;align-items:center;height:100vh;">
        <img src="/stream" style="max-width:100%;max-height:100%;" />
      </body>
    </html>
    """

if __name__ == "__main__":
    # Disable threading to avoid mss thread-safety issues
    app.run(host="0.0.0.0", port=8000, threaded=False)