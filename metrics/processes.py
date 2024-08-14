import psutil

def collect():
    metrics = {}

    try:
        total_process_count = len(psutil.pids())
        metrics['total_process_count'] = {'value': total_process_count}
    except Exception as e:
        metrics['total_process_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    try:
        running_process_count = len([p for p in psutil.process_iter(['status']) if p.info['status'] == psutil.STATUS_RUNNING])
        metrics['running_process_count'] = {'value': running_process_count}
    except Exception as e:
        metrics['running_process_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    try:
        zombie_process_count = len([p for p in psutil.process_iter(['status']) if p.info['status'] == psutil.STATUS_ZOMBIE])
        metrics['zombie_process_count'] = {'value': zombie_process_count}
    except Exception as e:
        metrics['zombie_process_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)