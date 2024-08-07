import os
import tempfile

def collect():
    temp_dir = tempfile.gettempdir()
    temp_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
    return len(temp_files)