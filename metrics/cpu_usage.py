import psutil

def collect():
    return psutil.cpu_percent()