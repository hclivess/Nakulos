import ssl
import socket
import datetime


def collect():
    hostname = 'google.com'
    port = 443

    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                cert = secure_sock.getpeercert()

        expire_date = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        days_left = (expire_date - datetime.datetime.utcnow()).days

        return days_left
    except Exception as e:
        return -1  # Return -1 to indicate an error