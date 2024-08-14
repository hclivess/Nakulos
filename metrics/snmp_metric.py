import socket
import struct
import time

def simple_snmp_get(host='localhost', port=161, oid=0, timeout=2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)

    try:
        start_time = time.time()
        sock.sendto(bytes([oid]), (host, port))
        data, _ = sock.recvfrom(1024)
        end_time = time.time()

        if len(data) != 4:
            return None, f"Received unexpected data length: {len(data)} bytes", end_time - start_time

        value = struct.unpack('!I', data)[0]
        return value, None, end_time - start_time
    except socket.timeout:
        return None, f"Timeout while querying {host} for OID {oid}", timeout
    except Exception as e:
        return None, f"Error querying {host} for OID {oid}: {str(e)}", 0
    finally:
        sock.close()

def collect(host='localhost', port=161):
    metrics = {}

    oids = {
        'sysUpTime': 0,
        'ifInOctets': 1,
        'ifOutOctets': 2,
        'cpuUsage': 3
    }

    total_time = 0

    for oid_name, oid in oids.items():
        value, error, query_time = simple_snmp_get(host=host, port=port, oid=oid)
        total_time += query_time

        if value is not None:
            metrics[oid_name] = {'value': value}
        else:
            metrics[oid_name] = {'value': None, 'message': error}

    metrics['total_query_time'] = {'value': total_time}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)