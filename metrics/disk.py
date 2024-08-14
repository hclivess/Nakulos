import psutil

def collect():
    metrics = {}

    # Get all disk partitions
    partitions = psutil.disk_partitions()

    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partition_name = partition.device.replace(':', '').replace('\\', '').replace('/', '_')

            metrics[f'{partition_name}_total'] = {
                'value': usage.total,
                'message': f"Total disk space for partition {partition_name}: {usage.total / (1024 ** 3):.2f} GB"
            }
            metrics[f'{partition_name}_used'] = {
                'value': usage.used,
                'message': f"Used disk space for partition {partition_name}: {usage.used / (1024 ** 3):.2f} GB"
            }
            metrics[f'{partition_name}_free'] = {
                'value': usage.free,
                'message': f"Free disk space for partition {partition_name}: {usage.free / (1024 ** 3):.2f} GB"
            }
            metrics[f'{partition_name}_percent'] = {
                'value': usage.percent,
                'message': f"Disk usage percentage for partition {partition_name}: {usage.percent}%"
            }
        except PermissionError:
            # Skip partitions that we don't have permission to access
            continue

    # Add overall I/O statistics
    io_counters = psutil.disk_io_counters()
    if io_counters:
        metrics['read_count'] = {
            'value': io_counters.read_count,
            'message': f"Total disk read count: {io_counters.read_count}"
        }
        metrics['write_count'] = {
            'value': io_counters.write_count,
            'message': f"Total disk write count: {io_counters.write_count}"
        }
        metrics['read_bytes'] = {
            'value': io_counters.read_bytes,
            'message': f"Total disk read bytes: {io_counters.read_bytes / (1024 ** 2):.2f} MB"
        }
        metrics['write_bytes'] = {
            'value': io_counters.write_bytes,
            'message': f"Total disk write bytes: {io_counters.write_bytes / (1024 ** 2):.2f} MB"
        }
        metrics['read_time'] = {
            'value': io_counters.read_time,
            'message': f"Total disk read time: {io_counters.read_time} ms"
        }
        metrics['write_time'] = {
            'value': io_counters.write_time,
            'message': f"Total disk write time: {io_counters.write_time} ms"
        }

    return metrics