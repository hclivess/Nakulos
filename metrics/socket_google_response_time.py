import socket
import time

def collect():
    try:
        start_time = time.time()
        socket.create_connection(("google.com", 80), timeout=5)
        end_time = time.time()
        return round((end_time - start_time) * 1000, 2)  # Return time in milliseconds
    except OSError:
        return -1  # Return -1 to indicate failure to connect