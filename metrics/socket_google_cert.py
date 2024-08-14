import ssl
import socket
import datetime


def collect():
    metrics = {}

    try:
        hostname = 'google.com'
        port = 443

        start_time = datetime.datetime.now()
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                cert = secure_sock.getpeercert()

        connection_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
        metrics['connection_time_ms'] = {'value': int(connection_time)}

        expire_date = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        days_until_expiry = (expire_date - datetime.datetime.utcnow()).days
        metrics['days_until_expiry'] = {'value': days_until_expiry}

        is_valid = 1 if days_until_expiry > 0 else 0
        metrics['is_valid'] = {'value': is_valid}

    except Exception as e:
        metrics['days_until_expiry'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['is_valid'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['connection_time_ms'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics


if __name__ == "__main__":
    result = collect()
    print(result)