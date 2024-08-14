import psutil
import time

def collect():
    metrics = {}

    try:
        current_time = time.time()
        boot_time = psutil.boot_time()
        uptime_seconds = int(current_time - boot_time)

        metrics['uptime_seconds'] = {'value': uptime_seconds}
        metrics['uptime_minutes'] = {'value': int(uptime_seconds / 60)}
        metrics['uptime_hours'] = {'value': int(uptime_seconds / 3600)}
        metrics['uptime_days'] = {'value': int(uptime_seconds / 86400)}
    except Exception as e:
        metrics['uptime_seconds'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['uptime_minutes'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['uptime_hours'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['uptime_days'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)