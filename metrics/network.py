import psutil

def collect():
    net_io = psutil.net_io_counters()
    return {
        'bytes_recv': net_io.bytes_recv,
        'bytes_sent': net_io.bytes_sent,
        'packets_recv': net_io.packets_recv,
        'packets_sent': net_io.packets_sent
    }

if __name__ == "__main__":
    network_metrics = collect()
    print(f"Bytes received: {network_metrics['bytes_recv']}")
    print(f"Bytes sent: {network_metrics['bytes_sent']}")
    print(f"Packets received: {network_metrics['packets_recv']}")
    print(f"Packets sent: {network_metrics['packets_sent']}")