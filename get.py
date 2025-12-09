import socket
import time
import vgamepad as vg

HOST = "0.0.0.0"
PORT = 5001

print(f"Listening on {HOST}:{PORT}...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

conn, addr = s.accept()
print(f"Client connected: {addr}")

# Create a virtual Xbox 360 controller
gamepad = vg.VX360Gamepad()

# Arrow escape sequences from Linux terminal
ESC_MAP = {
    "\x1b[A": "up",
    "\x1b[B": "down",
    "\x1b[C": "right",
    "\x1b[D": "left",
}

esc_buf = ""

# UPDATED CHARACTER MAP
CHAR_MAP = {
    "w": ("dpad", "up"),
    "s": ("dpad", "down"),
    "a": ("dpad", "left"),
    "d": ("dpad", "right"),

    # ★ Updated attack buttons (your requested mappings)
    "u": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_X),  # u -> X
    "i": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),  # i -> Y
    "j": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_A),  # j -> A
    "k": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_B),  # k -> B

    " ": ("button", vg.XUSB_BUTTON.XUSB_GAMEPAD_A),  # space → A (optional)
}

DPAD_MAP = {
    "up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}

def press_gamepad_action(kind, value, duration=0.05):
    """Press a gamepad button/dpad briefly."""
    try:
        if kind == "button":
            gamepad.press_button(button=value)
            gamepad.update()
            time.sleep(duration)
            gamepad.release_button(button=value)
            gamepad.update()

        elif kind == "dpad":
            btn = DPAD_MAP[value]
            gamepad.press_button(button=btn)
            gamepad.update()
            time.sleep(duration)
            gamepad.release_button(button=btn)
            gamepad.update()

    except Exception as e:
        print(f"Error sending gamepad action {kind} {value}: {e}")

try:
    while True:
        data = conn.recv(1024)
        if not data:
            print("Client disconnected")
            break

        for b in data:
            ch = chr(b)

            # Ctrl+C from client -> exit server
            if b == 3:
                print("Received Ctrl+C, shutting down server.")
                raise SystemExit

            # If we're currently building an escape sequence
            if esc_buf:
                esc_buf += ch

                if esc_buf in ESC_MAP:
                    direction = ESC_MAP[esc_buf]
                    print(f"ESC seq {repr(esc_buf)} -> dpad {direction}")
                    press_gamepad_action("dpad", direction)
                    esc_buf = ""
                    continue

                # If no ESC sequence starts with this prefix, discard it
                if not any(seq.startswith(esc_buf) for seq in ESC_MAP):
                    print(f"Unknown ESC seq {repr(esc_buf)}, discarding")
                    esc_buf = ""
                continue

            # Start of an escape sequence
            if ch == "\x1b":
                esc_buf = ch
                continue

            # Ignore newlines/carriage returns
            if ch in ("\n", "\r"):
                continue

            # Normal mapped keys
            if ch in CHAR_MAP:
                kind, value = CHAR_MAP[ch]
                print(f"Received raw: {repr(ch)} -> gamepad {kind} {value}")
                press_gamepad_action(kind, value)
            else:
                print(f"Received unmapped char: {repr(ch)} (no gamepad action)")

finally:
    conn.close()
    s.close()