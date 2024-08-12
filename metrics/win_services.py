import psutil


def collect():
    metrics = {
        'total_services': 0,
        'running_services': 0,
        'stopped_services': 0,
        'automatic_services': 0,
        'manual_services': 0,
        'disabled_services': 0
    }

    for service in psutil.win_service_iter():
        metrics['total_services'] += 1

        try:
            service_info = service.as_dict()

            if service_info['status'] == 'running':
                metrics['running_services'] += 1
            elif service_info['status'] == 'stopped':
                metrics['stopped_services'] += 1

            if service_info['start_type'] == 'automatic':
                metrics['automatic_services'] += 1
            elif service_info['start_type'] == 'manual':
                metrics['manual_services'] += 1
            elif service_info['start_type'] == 'disabled':
                metrics['disabled_services'] += 1
        except psutil.NoSuchProcess:
            # Service might have disappeared between listing and querying
            pass

    return metrics


if __name__ == "__main__":
    result = collect()
    print("Windows Services Statistics:")
    print(f"  Total services: {result['total_services']}")
    print(f"  Running services: {result['running_services']}")
    print(f"  Stopped services: {result['stopped_services']}")
    print(f"  Automatic start services: {result['automatic_services']}")
    print(f"  Manual start services: {result['manual_services']}")
    print(f"  Disabled services: {result['disabled_services']}")