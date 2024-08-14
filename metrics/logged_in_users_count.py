import psutil

def collect():
    metrics = {}

    try:
        user_count = len(psutil.users())
        metrics['user_count'] = {'value': user_count}
    except Exception as e:
        metrics['user_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)