import socket
import time

def collect():
    metrics = {}

    try:
        start_time = time.time()
        sock = socket.create_connection(("google.com", 80), timeout=5)
        sock.close()
        end_time = time.time()

        metrics['is_connected'] = {'value': 1}
        metrics['response_time_ms'] = {'value': int((end_time - start_time) * 1000)}
        metrics['error_code'] = {'value': 0}

    except socket.timeout:
        metrics['is_connected'] = {'value': 0}
        metrics['response_time_ms'] = {'value': None}
        metrics['error_code'] = {'value': 1, 'message': "SocketTimeout: Connection timed out"}

    except socket.gaierror:
        metrics['is_connected'] = {'value': 0}
        metrics['response_time_ms'] = {'value': None}
        metrics['error_code'] = {'value': 2, 'message': "SocketGAIError: Failed to resolve hostname"}

    except OSError:
        metrics['is_connected'] = {'value': 0}
        metrics['response_time_ms'] = {'value': None}
        metrics['error_code'] = {'value': 3, 'message': "OSError: Failed to create or close the socket"}

    except Exception as e:
        metrics['is_connected'] = {'value': 0}
        metrics['response_time_ms'] = {'value': None}
        metrics['error_code'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)