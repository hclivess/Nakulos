import psutil
import time

def collect():
    current_time = time.time()
    boot_time = psutil.boot_time()
    uptime_seconds = current_time - boot_time

    return {
        'uptime_seconds': int(uptime_seconds),
        'uptime_minutes': int(uptime_seconds / 60),
        'uptime_hours': int(uptime_seconds / 3600),
        'uptime_days': int(uptime_seconds / 86400)
    }

if __name__ == "__main__":
    result = collect()
    print(f"System uptime:")
    print(f"  {result['uptime_seconds']} seconds")
    print(f"  {result['uptime_minutes']} minutes")
    print(f"  {result['uptime_hours']} hours")
    print(f"  {result['uptime_days']} days")