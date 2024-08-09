import psutil

def collect():
    cpu_times_percent = psutil.cpu_times_percent()
    return {
        'cpu_percent': psutil.cpu_percent(),
        'cpu_user': cpu_times_percent.user,
        'cpu_system': cpu_times_percent.system,
        'cpu_idle': cpu_times_percent.idle,
        'cpu_iowait': cpu_times_percent.iowait if hasattr(cpu_times_percent, 'iowait') else None,
        'cpu_irq': cpu_times_percent.irq if hasattr(cpu_times_percent, 'irq') else None,
        'cpu_softirq': cpu_times_percent.softirq if hasattr(cpu_times_percent, 'softirq') else None,
        'cpu_steal': cpu_times_percent.steal if hasattr(cpu_times_percent, 'steal') else None,
        'cpu_guest': cpu_times_percent.guest if hasattr(cpu_times_percent, 'guest') else None
    }