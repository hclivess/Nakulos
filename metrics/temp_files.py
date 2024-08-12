import os
import tempfile

def collect():
    temp_dir = tempfile.gettempdir()
    metrics = {
        'file_count': 0,
        'dir_count': 0,
        'total_size_bytes': 0,
        'oldest_file_age_seconds': 0,
        'newest_file_age_seconds': float('inf')
    }

    current_time = os.time()

    for entry in os.scandir(temp_dir):
        if entry.is_file():
            metrics['file_count'] += 1
            stats = entry.stat()
            metrics['total_size_bytes'] += stats.st_size
            age = current_time - stats.st_mtime
            metrics['oldest_file_age_seconds'] = max(metrics['oldest_file_age_seconds'], age)
            metrics['newest_file_age_seconds'] = min(metrics['newest_file_age_seconds'], age)
        elif entry.is_dir():
            metrics['dir_count'] += 1

    # If no files were found, set newest_file_age_seconds to 0
    if metrics['newest_file_age_seconds'] == float('inf'):
        metrics['newest_file_age_seconds'] = 0

    return metrics

if __name__ == "__main__":
    result = collect()
    print(f"Temporary directory statistics:")
    print(f"  File count: {result['file_count']}")
    print(f"  Directory count: {result['dir_count']}")
    print(f"  Total size: {result['total_size_bytes']} bytes")
    print(f"  Oldest file age: {result['oldest_file_age_seconds']:.2f} seconds")
    print(f"  Newest file age: {result['newest_file_age_seconds']:.2f} seconds")