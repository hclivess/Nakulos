import psutil

def collect():
    return len(psutil.users())