import psutil

def collect():
    return psutil.net_io_counters().bytes_sent