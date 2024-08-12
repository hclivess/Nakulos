import ssl
import socket
import datetime

def collect():
    hostname = 'google.com'
    port = 443
    metrics = {
        'days_until_expiry': -1,
        'is_valid': 0,
        'connection_time_ms': 0
    }

    try:
        start_time = datetime.datetime.now()
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                cert = secure_sock.getpeercert()

        connection_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
        metrics['connection_time_ms'] = int(connection_time)

        expire_date = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        metrics['days_until_expiry'] = (expire_date - datetime.datetime.utcnow()).days
        metrics['is_valid'] = 1 if metrics['days_until_expiry'] > 0 else 0

    except Exception as e:
        metrics['days_until_expiry'] = -1
        metrics['is_valid'] = 0

    return metrics

if __name__ == "__main__":
    result = collect()
    print(f"Days until certificate expiry: {result['days_until_expiry']}")
    print(f"Certificate is valid: {'Yes' if result['is_valid'] == 1 else 'No'}")
    print(f"Connection time: {result['connection_time_ms']} ms")