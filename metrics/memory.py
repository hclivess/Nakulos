import psutil

def collect():
    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()

    return {
        'virtual_memory_percent': {
            'value': virtual_memory.percent,
            'message': f"Virtual Memory Usage: {virtual_memory.percent}%"
        },
        'virtual_memory_available': {
            'value': virtual_memory.available,
            'message': f"Available Virtual Memory: {virtual_memory.available / (1024 * 1024):.2f} MB"
        },
        'virtual_memory_used': {
            'value': virtual_memory.used,
            'message': f"Used Virtual Memory: {virtual_memory.used / (1024 * 1024):.2f} MB"
        },
        'virtual_memory_free': {
            'value': virtual_memory.free,
            'message': f"Free Virtual Memory: {virtual_memory.free / (1024 * 1024):.2f} MB"
        },
        'swap_memory_percent': {
            'value': swap_memory.percent,
            'message': f"Swap Memory Usage: {swap_memory.percent}%"
        },
        'swap_memory_used': {
            'value': swap_memory.used,
            'message': f"Used Swap Memory: {swap_memory.used / (1024 * 1024):.2f} MB"
        },
        'swap_memory_free': {
            'value': swap_memory.free,
            'message': f"Free Swap Memory: {swap_memory.free / (1024 * 1024):.2f} MB"
        }
    }

if __name__ == "__main__":
    memory_metrics = collect()
    for metric, data in memory_metrics.items():
        print(data['message'])