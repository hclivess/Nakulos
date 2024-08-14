import psutil

def collect():
    metrics = {}

    try:
        total_services = 0
        running_services = 0
        stopped_services = 0
        automatic_services = 0
        manual_services = 0
        disabled_services = 0

        for service in psutil.win_service_iter():
            total_services += 1

            try:
                service_info = service.as_dict()

                if service_info['status'] == 'running':
                    running_services += 1
                elif service_info['status'] == 'stopped':
                    stopped_services += 1

                if service_info['start_type'] == 'automatic':
                    automatic_services += 1
                elif service_info['start_type'] == 'manual':
                    manual_services += 1
                elif service_info['start_type'] == 'disabled':
                    disabled_services += 1
            except psutil.NoSuchProcess:
                pass

        metrics['total_services'] = {'value': total_services}
        metrics['running_services'] = {'value': running_services}
        metrics['stopped_services'] = {'value': stopped_services}
        metrics['automatic_services'] = {'value': automatic_services}
        metrics['manual_services'] = {'value': manual_services}
        metrics['disabled_services'] = {'value': disabled_services}
    except Exception as e:
        metrics['total_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['running_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['stopped_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['automatic_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['manual_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['disabled_services'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)