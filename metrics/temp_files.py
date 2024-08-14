import os
import tempfile

def collect():
    metrics = {}

    try:
        temp_dir = tempfile.gettempdir()
        file_count = 0
        dir_count = 0
        total_size_bytes = 0
        oldest_file_age_seconds = 0
        newest_file_age_seconds = float('inf')

        current_time = os.time()

        for entry in os.scandir(temp_dir):
            if entry.is_file():
                file_count += 1
                stats = entry.stat()
                total_size_bytes += stats.st_size
                age = current_time - stats.st_mtime
                oldest_file_age_seconds = max(oldest_file_age_seconds, age)
                newest_file_age_seconds = min(newest_file_age_seconds, age)
            elif entry.is_dir():
                dir_count += 1

        if newest_file_age_seconds == float('inf'):
            newest_file_age_seconds = 0

        metrics['file_count'] = {'value': file_count}
        metrics['dir_count'] = {'value': dir_count}
        metrics['total_size_bytes'] = {'value': total_size_bytes}
        metrics['oldest_file_age_seconds'] = {'value': oldest_file_age_seconds}
        metrics['newest_file_age_seconds'] = {'value': newest_file_age_seconds}
    except Exception as e:
        metrics['file_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['dir_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['total_size_bytes'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['oldest_file_age_seconds'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['newest_file_age_seconds'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)