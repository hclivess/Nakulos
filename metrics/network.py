import psutil

def collect():
    metrics = {}

    try:
        net_io = psutil.net_io_counters()

        try:
            bytes_recv = net_io.bytes_recv
            metrics['bytes_recv'] = {'value': bytes_recv}
        except Exception as e:
            metrics['bytes_recv'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

        try:
            bytes_sent = net_io.bytes_sent
            metrics['bytes_sent'] = {'value': bytes_sent}
        except Exception as e:
            metrics['bytes_sent'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

        try:
            packets_recv = net_io.packets_recv
            metrics['packets_recv'] = {'value': packets_recv}
        except Exception as e:
            metrics['packets_recv'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

        try:
            packets_sent = net_io.packets_sent
            metrics['packets_sent'] = {'value': packets_sent}
        except Exception as e:
            metrics['packets_sent'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    except Exception as e:
        metrics['bytes_recv'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['bytes_sent'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['packets_recv'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['packets_sent'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)