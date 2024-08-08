import psutil
import time

def collect():
    return time.time() - psutil.boot_time()