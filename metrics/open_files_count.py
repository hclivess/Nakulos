import psutil

def collect():
    return len(psutil.Process().open_files())