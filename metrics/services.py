import psutil
import platform

def collect():
    metrics = {}

    if platform.system() == 'Windows':
        try:
            total_services = 0
            running_services = 0
            stopped_services = 0

            for service in psutil.win_service_iter():
                total_services += 1
                try:
                    service_info = service.as_dict()
                    if service_info['status'] == 'running':
                        running_services += 1
                    elif service_info['status'] == 'stopped':
                        stopped_services += 1
                except psutil.NoSuchProcess:
                    pass

            metrics['total_services'] = {'value': total_services}
            metrics['running_services'] = {'value': running_services}
            metrics['stopped_services'] = {'value': stopped_services}
        except Exception as e:
            metrics['total_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
            metrics['running_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
            metrics['stopped_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    elif platform.system() == 'Linux':
        try:
            total_services = 0
            running_services = 0
            stopped_services = 0

            for unit in psutil.process_iter(['name', 'status']):
                try:
                    if unit.name().endswith('.service'):
                        total_services += 1
                        if unit.status() == psutil.STATUS_RUNNING:
                            running_services += 1
                        else:
                            stopped_services += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            metrics['total_services'] = {'value': total_services}
            metrics['running_services'] = {'value': running_services}
            metrics['stopped_services'] = {'value': stopped_services}
        except Exception as e:
            metrics['total_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
            metrics['running_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
            metrics['stopped_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)