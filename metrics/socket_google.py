import socket
import time


def collect():
    metrics = {
        'is_connected': 0,
        'response_time_ms': 0,
        'error_code': 0
    }

    start_time = time.time()
    try:
        sock = socket.create_connection(("google.com", 80), timeout=5)
        sock.close()
        end_time = time.time()

        metrics['is_connected'] = 1
        metrics['response_time_ms'] = int((end_time - start_time) * 1000)
    except socket.timeout:
        metrics['error_code'] = 1
    except socket.gaierror:
        metrics['error_code'] = 2
    except OSError:
        metrics['error_code'] = 3

    return metrics


if __name__ == "__main__":
    result = collect()
    print(f"Connection status: {'Successful' if result['is_connected'] == 1 else 'Failed'}")
    print(f"Response time: {result['response_time_ms']} ms")
    print(f"Error code: {result['error_code']}")