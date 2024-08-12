import psutil

def collect():
    current_process = psutil.Process()
    return {
        'open_files_count': len(current_process.open_files()),
        'fd_count': current_process.num_fds() if hasattr(current_process, 'num_fds') else None,
        'connections_count': len(current_process.connections())
    }

if __name__ == "__main__":
    fd_metrics = collect()
    print(f"Open files count: {fd_metrics['open_files_count']}")
    if fd_metrics['fd_count'] is not None:
        print(f"File descriptor count: {fd_metrics['fd_count']}")
    else:
        print("File descriptor count not available on this system")
    print(f"Open connections count: {fd_metrics['connections_count']}")