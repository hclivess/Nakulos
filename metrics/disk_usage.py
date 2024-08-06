import psutil

def collect():
    return psutil.disk_usage('/').percent