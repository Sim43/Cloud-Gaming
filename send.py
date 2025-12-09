import socket
import sys
import termios
import tty

SERVER_IP = "192.168.100.132"
PORT = 5001

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((SERVER_IP, PORT))

print("Connected. Press keys (Ctrl+C to exit):")

old_settings = termios.tcgetattr(sys.stdin)

try:
    tty.setraw(sys.stdin.fileno())

    while True:
        char = sys.stdin.read(1)
        s.send(char.encode())
        if ord(char) == 3:  # Ctrl+C
            break

finally:
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    s.close()
