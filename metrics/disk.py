import psutil


def collect():
    metrics = {}

    # Get all disk partitions
    partitions = psutil.disk_partitions()

    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partition_name = partition.device.replace(':', '').replace('\\', '').replace('/', '_')

            metrics[f'{partition_name}_total'] = usage.total
            metrics[f'{partition_name}_used'] = usage.used
            metrics[f'{partition_name}_free'] = usage.free
            metrics[f'{partition_name}_percent'] = usage.percent
        except PermissionError:
            # Skip partitions that we don't have permission to access
            continue

    # Add overall I/O statistics
    io_counters = psutil.disk_io_counters()
    if io_counters:
        metrics['read_count'] = io_counters.read_count
        metrics['write_count'] = io_counters.write_count
        metrics['read_bytes'] = io_counters.read_bytes
        metrics['write_bytes'] = io_counters.write_bytes
        metrics['read_time'] = io_counters.read_time
        metrics['write_time'] = io_counters.write_time

    return metrics