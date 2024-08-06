import psutil

def collect():
    return psutil.virtual_memory().percent