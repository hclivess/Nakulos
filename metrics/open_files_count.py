import psutil

def collect():
    metrics = {}

    try:
        current_process = psutil.Process()

        try:
            open_files_count = len(current_process.open_files())
            metrics['open_files_count'] = {'value': open_files_count}
        except Exception as e:
            metrics['open_files_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

        try:
            fd_count = current_process.num_fds() if hasattr(current_process, 'num_fds') else None
            if fd_count is not None:
                metrics['fd_count'] = {'value': fd_count}
            else:
                metrics['fd_count'] = {'value': None, 'message': "File descriptor count not available on this system"}
        except Exception as e:
            metrics['fd_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

        try:
            connections_count = len(current_process.connections())
            metrics['connections_count'] = {'value': connections_count}
        except Exception as e:
            metrics['connections_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    except Exception as e:
        metrics['open_files_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['fd_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['connections_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)