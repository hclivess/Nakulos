import psutil
import platform

def collect():
    metrics = {
        'total_services': 0,
        'running_services': 0,
        'stopped_services': 0
    }

    if platform.system() == 'Windows':
        for service in psutil.win_service_iter():
            metrics['total_services'] += 1
            try:
                service_info = service.as_dict()
                if service_info['status'] == 'running':
                    metrics['running_services'] += 1
                elif service_info['status'] == 'stopped':
                    metrics['stopped_services'] += 1
            except psutil.NoSuchProcess:
                pass
    elif platform.system() == 'Linux':
        for unit in psutil.process_iter(['name', 'status']):
            try:
                if unit.name().endswith('.service'):
                    metrics['total_services'] += 1
                    if unit.status() == psutil.STATUS_RUNNING:
                        metrics['running_services'] += 1
                    else:
                        metrics['stopped_services'] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    return metrics

if __name__ == "__main__":
    result = collect()
    print(f"Operating System: {platform.system()}")
    print(f"Total services: {result['total_services']}")
    print(f"Running services: {result['running_services']}")
    print(f"Stopped services: {result['stopped_services']}")