"""Utility functions for IP detection and network operations."""
import socket


def get_local_ip():
    """
    Get the local IP address of the machine.
    Returns the IP address that can be used for server connections.
    """
    try:
        # Connect to a remote address (doesn't actually send data)
        # This gets the IP address of the interface used to reach that address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback: try to get hostname IP
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except Exception:
            return "127.0.0.1"

