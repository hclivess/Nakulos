import socket

def collect():
    try:
        socket.create_connection(("google.com", 80), timeout=5)
        return 1
    except OSError:
        return 0