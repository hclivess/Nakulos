import psutil

def collect():
    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()

    return {
        'virtual_memory_percent': {
            'value': virtual_memory.percent,
        },
        'virtual_memory_available': {
            'value': virtual_memory.available,
        },
        'virtual_memory_used': {
            'value': virtual_memory.used,
        },
        'virtual_memory_free': {
            'value': virtual_memory.free,
        },
        'swap_memory_percent': {
            'value': swap_memory.percent,
        },
        'swap_memory_used': {
            'value': swap_memory.used,
        },
        'swap_memory_free': {
            'value': swap_memory.free,
        }
    }

if __name__ == "__main__":
    memory_metrics = collect()
    for metric, data in memory_metrics.items():
        print(data['message'])