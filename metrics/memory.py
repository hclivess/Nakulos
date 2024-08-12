import psutil


def collect():
    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()

    return {
        'virtual_memory_percent': virtual_memory.percent,
        'virtual_memory_available': virtual_memory.available,
        'virtual_memory_used': virtual_memory.used,
        'virtual_memory_free': virtual_memory.free,
        'swap_memory_percent': swap_memory.percent,
        'swap_memory_used': swap_memory.used,
        'swap_memory_free': swap_memory.free
    }


if __name__ == "__main__":
    memory_metrics = collect()
    print(f"Virtual Memory Usage: {memory_metrics['virtual_memory_percent']}%")
    print(f"Available Virtual Memory: {memory_metrics['virtual_memory_available'] / (1024 * 1024):.2f} MB")
    print(f"Used Virtual Memory: {memory_metrics['virtual_memory_used'] / (1024 * 1024):.2f} MB")
    print(f"Free Virtual Memory: {memory_metrics['virtual_memory_free'] / (1024 * 1024):.2f} MB")
    print(f"Swap Memory Usage: {memory_metrics['swap_memory_percent']}%")
    print(f"Used Swap Memory: {memory_metrics['swap_memory_used'] / (1024 * 1024):.2f} MB")
    print(f"Free Swap Memory: {memory_metrics['swap_memory_free'] / (1024 * 1024):.2f} MB")