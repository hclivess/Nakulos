import psutil

def collect():
    return {
        'total_process_count': len(psutil.pids()),
        'running_process_count': len([p for p in psutil.process_iter(['status']) if p.info['status'] == psutil.STATUS_RUNNING]),
        'zombie_process_count': len([p for p in psutil.process_iter(['status']) if p.info['status'] == psutil.STATUS_ZOMBIE])
    }

if __name__ == "__main__":
    process_metrics = collect()
    print(f"Total process count: {process_metrics['total_process_count']}")
    print(f"Running process count: {process_metrics['running_process_count']}")
    print(f"Zombie process count: {process_metrics['zombie_process_count']}")