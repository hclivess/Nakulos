import psutil

def collect():
    cpu_times_percent = psutil.cpu_times_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    cpu_count = psutil.cpu_count()

    return {
        'cpu_percent': {
            'value': psutil.cpu_percent(interval=1),
            'message': f"CPU Utilization: {psutil.cpu_percent(interval=1)}%"
        },
        'cpu_user': {
            'value': cpu_times_percent.user,
            'message': f"CPU User Time: {cpu_times_percent.user}%"
        },
        'cpu_system': {
            'value': cpu_times_percent.system,
            'message': f"CPU System Time: {cpu_times_percent.system}%"
        },
        'cpu_idle': {
            'value': cpu_times_percent.idle,
            'message': f"CPU Idle Time: {cpu_times_percent.idle}%"
        },
        'cpu_iowait': {
            'value': cpu_times_percent.iowait if hasattr(cpu_times_percent, 'iowait') else None,
            'message': f"CPU I/O Wait Time: {cpu_times_percent.iowait}%" if hasattr(cpu_times_percent, 'iowait') else None
        },
        'cpu_irq': {
            'value': cpu_times_percent.irq if hasattr(cpu_times_percent, 'irq') else None,
            'message': f"CPU IRQ Time: {cpu_times_percent.irq}%" if hasattr(cpu_times_percent, 'irq') else None
        },
        'cpu_softirq': {
            'value': cpu_times_percent.softirq if hasattr(cpu_times_percent, 'softirq') else None,
            'message': f"CPU SoftIRQ Time: {cpu_times_percent.softirq}%" if hasattr(cpu_times_percent, 'softirq') else None
        },
        'cpu_steal': {
            'value': cpu_times_percent.steal if hasattr(cpu_times_percent, 'steal') else None,
            'message': f"CPU Stolen Time: {cpu_times_percent.steal}%" if hasattr(cpu_times_percent, 'steal') else None
        },
        'cpu_guest': {
            'value': cpu_times_percent.guest if hasattr(cpu_times_percent, 'guest') else None,
            'message': f"CPU Guest Time: {cpu_times_percent.guest}%" if hasattr(cpu_times_percent, 'guest') else None
        },
        'cpu_freq_current': {
            'value': cpu_freq.current if hasattr(cpu_freq, 'current') else None,
            'message': f"Current CPU Frequency: {cpu_freq.current} MHz" if hasattr(cpu_freq, 'current') else None
        },
        'cpu_freq_min': {
            'value': cpu_freq.min if hasattr(cpu_freq, 'min') else None,
            'message': f"Minimum CPU Frequency: {cpu_freq.min} MHz" if hasattr(cpu_freq, 'min') else None
        },
        'cpu_freq_max': {
            'value': cpu_freq.max if hasattr(cpu_freq, 'max') else None,
            'message': f"Maximum CPU Frequency: {cpu_freq.max} MHz" if hasattr(cpu_freq, 'max') else None
        },
        'cpu_count': {
            'value': cpu_count,
            'message': f"Number of CPU Cores: {cpu_count}"
        }
    }