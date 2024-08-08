import psutil

def collect():
    return len(list(psutil.win_service_iter()))